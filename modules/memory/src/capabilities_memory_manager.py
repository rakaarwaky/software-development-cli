"""Memory file manager capability (AES capabilities layer).

Ported from ``skills/software-development/implement/scripts/memory.py``.

Implements the ``IMemoryAggregate`` contract: workspace-scoped path
resolution, concurrency-safe atomic writes, and deterministic dedup +
compaction.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shared.src.common.taxonomy_sdc_constant import (
    CATEGORY_RE,
    DEFAULT_HEADER,
    FILE_MODE,
    GIT_TIMEOUT_SECONDS,
    ISSUE_RE,
    LOCK_POLL_INTERVAL,
    LOCK_TIMEOUT_SECONDS,
    MAX_PATTERNS_PER_CATEGORY,
    MAX_RECENT_RUNS,
    MEMORY_SUBDIR,
    RUN_RE,
    SECTION_COMMON_ISSUES_RE,
    SECTION_RECENT_RUNS_RE,
    SEVERITY_ORDER,
)
from shared.src.common.taxonomy_sdc_error import (
    LockTimeoutError,
    MemoryHelperError,
    SpecError,
    WorkspaceIdError,
)
from shared.src.common.utility_sdc_common import (
    canonicalize_remote,
    git_output,
    normalize,
    repo_slug,
    sanitize_one_line,
)
from shared.src.memory.contract_memory_aggregate import IMemoryAggregate
from shared.src.memory.taxonomy_memory_request import MemoryRequest, MemoryResult


class MemoryStore(IMemoryAggregate):
    """Concrete memory store implementing ``IMemoryAggregate``."""

    def execute(self, request: MemoryRequest) -> MemoryResult:
        if request.action == "path":
            return MemoryResult(path=str(memory_paths()["file"]))
        if request.action == "read":
            f = memory_paths()["file"]
            content = f.read_text(encoding="utf-8") if f.exists() else ""
            return MemoryResult(content=content)
        if request.action == "snapshot":
            f = memory_paths()["file"]
            if f.exists():
                state = parse_memory_file(f.read_text(encoding="utf-8"))
                payload = _build_snapshot(state, exists=True)
            else:
                payload = _build_snapshot(
                    {"header": [], "common_issues": OrderedDict(), "recent_runs": []},
                    exists=False,
                )
            return MemoryResult(snapshot=payload)
        if request.action == "update":
            return _update(request)
        raise SpecError(
            f"memory: unknown action {request.action!r}; "
            f"expected 'path', 'read', 'snapshot', or 'update'"
        )


# ─── Block 1: Module Declaration ───────────────────────────────────────

# ─── Workspace identification ─────────────────────────────────────────


def get_workspace_id() -> str:
    """Return ``"<readable-name>-<hash12>"`` identifying this workspace.

    Source preference: canonicalised git remote origin URL → absolute
    path of ``.git`` common dir → absolute cwd. Raises ``WorkspaceIdError``
    if all three are unusable.
    """
    raw_remote = git_output("config", "--get", "remote.origin.url")
    id_source = canonicalize_remote(raw_remote) if raw_remote else ""

    if not id_source:
        common_dir = git_output("rev-parse", "--git-common-dir")
        if common_dir:
            try:
                id_source = str(Path(common_dir).resolve(strict=False))
            except OSError:
                id_source = common_dir

    if not id_source:
        try:
            id_source = str(Path.cwd().resolve())
        except (OSError, FileNotFoundError):
            raise WorkspaceIdError(
                "could not determine workspace id (no git repo, no remote, no usable cwd)"
            )

    digest = hashlib.sha256(id_source.encode("utf-8")).hexdigest()[:12]

    raw_name = id_source.rstrip("/").rsplit("/", 1)[-1]
    if raw_name.endswith(".git"):
        raw_name = raw_name[:-4]
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in raw_name)
    safe_name = safe_name.strip("_.-")[:40].rstrip("_.-") or "workspace"

    return f"{safe_name}-{digest}"


def memory_paths(*, create_dir: bool = False) -> dict[str, Path]:
    """Return ``{"dir", "file", "lock"}`` for this repo.

    Path is ``~/.agents/develop/<reponame>/memory/<reponame>-<hash12>.md``,
    matching the per-repo artifact root layout used by the other skills.

    Raises ``WorkspaceIdError`` on unrecoverable HOME / workspace-id failures.
    """
    try:
        home = Path.home()
    except RuntimeError:
        raise WorkspaceIdError(
            "could not determine the user's home directory ($HOME unset and pwd lookup failed)"
        )
    try:
        slug = repo_slug()
    except Exception as exc:
        raise WorkspaceIdError(f"could not determine repo slug: {exc}")
    base = home / ".agents" / "develop" / slug / MEMORY_SUBDIR
    if create_dir:
        try:
            base.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise WorkspaceIdError(f"could not create memory directory {base}: {exc}")
    workspace_id = get_workspace_id()
    return {
        "dir": base,
        "file": base / f"{workspace_id}.md",
        "lock": base / f"{workspace_id}.lock",
    }


# ─── Type validation helpers ──────────────────────────────────────────


def _require_str(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise SpecError(f'"{field}" must be a string, got {type(value).__name__}')
    return value


def _require_optional_str(value: Any, field: str) -> str:
    if value is None:
        return ""
    return _require_str(value, field)


def _require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise SpecError(f'"{field}" must be a list, got {type(value).__name__}')
    return value


def _require_dict(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SpecError(f'"{field}" must be an object, got {type(value).__name__}')
    return value


def _require_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SpecError(f'"{field}" must be an integer, got {type(value).__name__}')
    return value


# ─── Markdown parsing & rendering ─────────────────────────────────────


def parse_memory_file(content: str) -> dict[str, Any]:
    """Parse the memory file into a structured dict.

    Returns ``{"header": [...], "common_issues": {cat: [{desc, count}]}, "recent_runs": [...]}``.
    """
    state: dict[str, Any] = {
        "header": [],
        "common_issues": OrderedDict(),
        "recent_runs": [],
    }

    if not content.strip():
        return state

    section = "header"
    current_category: str | None = None
    current_run: dict[str, Any] | None = None

    for line in content.splitlines():
        if SECTION_COMMON_ISSUES_RE.match(line):
            if current_run is not None:
                state["recent_runs"].append(current_run)
                current_run = None
            section = "common_issues"
            current_category = None
            continue
        if SECTION_RECENT_RUNS_RE.match(line):
            if current_run is not None:
                state["recent_runs"].append(current_run)
                current_run = None
            section = "recent_runs"
            current_category = None
            continue

        if section == "header":
            state["header"].append(line)
            continue

        if section == "common_issues":
            cat_match = CATEGORY_RE.match(line)
            if cat_match:
                current_category = cat_match.group(1).strip()
                state["common_issues"].setdefault(current_category, [])
                continue
            issue_match = ISSUE_RE.match(line)
            if issue_match and current_category is not None:
                state["common_issues"][current_category].append(
                    {
                        "description": issue_match.group(1).strip(),
                        "count": int(issue_match.group(2)),
                    }
                )
            continue

        if section == "recent_runs":
            run_match = RUN_RE.match(line)
            if run_match:
                if current_run is not None:
                    state["recent_runs"].append(current_run)
                current_run = {
                    "date": run_match.group(1),
                    "description": run_match.group(2).strip(),
                    "body_lines": [],
                }
                continue
            if current_run is not None:
                current_run["body_lines"].append(line)

    if current_run is not None:
        state["recent_runs"].append(current_run)

    state["header"] = _drop_trailing_blank(state["header"])
    for run in state["recent_runs"]:
        run["body_lines"] = _drop_trailing_blank(run["body_lines"])
    return state


def _drop_trailing_blank(lines: list[str]) -> list[str]:
    """Return a new list with trailing blank/whitespace-only lines removed."""
    end = len(lines)
    while end > 0 and not lines[end - 1].strip():
        end -= 1
    return list(lines[:end])


def render_memory_file(state: dict[str, Any]) -> str:
    """Render the parsed state back to markdown."""
    out: list[str] = []

    header = state.get("header") or list(DEFAULT_HEADER)
    out.extend(_drop_trailing_blank(header))
    out.append("")

    out.append("## Common Issues")
    out.append("")
    has_any = any(entries for entries in state["common_issues"].values())
    if not has_any:
        out.append("_No patterns recorded yet._")
        out.append("")
    else:
        for category, entries in state["common_issues"].items():
            if not entries:
                continue
            out.append(f"### {category}")
            for e in entries:
                times = "time" if e["count"] == 1 else "times"
                out.append(f"- {e['description']} (seen {e['count']} {times})")
            out.append("")

    out.append("## Recent Runs")
    out.append("")
    for run in state["recent_runs"]:
        out.append(f"### {run['date']} — {run['description']}")
        out.extend(_drop_trailing_blank(run.get("body_lines") or []))
        out.append("")

    return "\n".join(out).rstrip() + "\n"


# ─── Merge logic ──────────────────────────────────────────────────────


def _format_severity_summary(ibs: dict[str, int]) -> tuple[str, int]:
    """Render ``"3 bugs, 4 suggestions"`` and return the total."""
    parts: list[str] = []
    rendered_total = 0
    seen: set[str] = set()
    for sev in SEVERITY_ORDER:
        if sev in ibs:
            count = ibs[sev]
            seen.add(sev)
            if count > 0:
                label = sev if count == 1 else f"{sev}s"
                parts.append(f"{count} {label}")
                rendered_total += count
    for sev in sorted(ibs):
        if sev in seen:
            continue
        count = ibs[sev]
        if count > 0:
            label = sev if count == 1 else f"{sev}s"
            parts.append(f"{count} {label}")
            rendered_total += count
    return ", ".join(parts), rendered_total


def _bump_or_append(
    entries: list[dict[str, Any]],
    lookup: dict[str, dict[str, Any]],
    description: str,
) -> bool:
    """Increment matching entry's count, or append a new one. Returns True on match."""
    norm_new = normalize(description)
    match = lookup.get(norm_new)
    if match is not None:
        match["count"] += 1
        return True
    new_entry = {"description": description, "count": 1}
    entries.append(new_entry)
    lookup[norm_new] = new_entry
    return False


def _canonical_category(existing: Any, name: str) -> str:
    """Return the existing category matching ``name`` ignoring case and whitespace runs."""
    from shared.src.common.taxonomy_sdc_constant import WHITESPACE_RE

    key = WHITESPACE_RE.sub(" ", name).strip().lower()
    for have in existing:
        if WHITESPACE_RE.sub(" ", have).strip().lower() == key:
            return have
    return name


def merge_run(state: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    """Merge a run spec into ``state`` in place. Return summary stats."""
    stats: dict[str, Any] = {
        "new_patterns": 0,
        "merged_patterns": 0,
        "categories_touched": [],
        "categories_capped": {},
        "recent_runs_dropped": 0,
    }
    touched: set[str] = set()
    category_lookups: dict[str, dict[str, dict[str, Any]]] = {}

    patterns = spec.get("patterns")
    if patterns is not None:
        patterns = _require_list(patterns, "patterns")
        for idx, raw in enumerate(patterns):
            field = f"patterns[{idx}]"
            raw = _require_dict(raw, field)

            category_raw = raw.get("category")
            if category_raw is None or category_raw == "":
                category = "Other"
            else:
                category = sanitize_one_line(_require_str(category_raw, f"{field}.category"))
                if not category:
                    category = "Other"

            description = sanitize_one_line(
                _require_optional_str(raw.get("description"), f"{field}.description")
            )
            if not description:
                continue

            category = _canonical_category(state["common_issues"], category)
            entries = state["common_issues"].setdefault(category, [])
            lookup = category_lookups.get(category)
            if lookup is None:
                lookup = {normalize(e["description"]): e for e in entries}
                category_lookups[category] = lookup
            if _bump_or_append(entries, lookup, description):
                stats["merged_patterns"] += 1
            else:
                stats["new_patterns"] += 1
            touched.add(category)

    for category, entries in state["common_issues"].items():
        entries.sort(key=lambda e: (-e["count"], e["description"].lower()))
        if len(entries) > MAX_PATTERNS_PER_CATEGORY:
            dropped = len(entries) - MAX_PATTERNS_PER_CATEGORY
            del entries[MAX_PATTERNS_PER_CATEGORY:]
            stats["categories_capped"][category] = dropped

    run_raw = spec.get("run")
    if run_raw is not None:
        run = _require_dict(run_raw, "run")
        if run:
            _merge_recent_run(state, run, stats)

    stats["categories_touched"] = sorted(touched)
    return stats


def _merge_recent_run(state: dict[str, Any], run: dict[str, Any], stats: dict[str, Any]) -> None:
    """Validate and prepend a Recent Runs entry. Updates ``stats`` in place."""
    date_raw = run.get("date")
    if date_raw is None or (isinstance(date_raw, str) and not date_raw.strip()):
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    else:
        date_str = _require_str(date_raw, "run.date").strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise SpecError(
                f'"run.date" must be a calendar-valid YYYY-MM-DD date, got {date_str!r}'
            )
        date = date_str

    desc_raw = run.get("description")
    description = (
        sanitize_one_line(_require_optional_str(desc_raw, "run.description")) or "(no description)"
    )
    description = description.replace('"', "").strip() or "(no description)"
    description = f'"{description}"'

    body_lines: list[str] = []

    rounds_raw = run.get("rounds")
    if rounds_raw is not None:
        rounds = _require_int(rounds_raw, "run.rounds")
        body_lines.append(f"- **Rounds**: {rounds}")

    ibs_raw = run.get("issues_by_severity")
    if ibs_raw is not None:
        ibs = _require_dict(ibs_raw, "run.issues_by_severity")
        normalized_ibs: dict[str, int] = {}
        for sev, count in ibs.items():
            if not isinstance(sev, str):
                raise SpecError(
                    f'"run.issues_by_severity" keys must be strings, got {type(sev).__name__}'
                )
            normalized_ibs[sev] = _require_int(count, f'run.issues_by_severity["{sev}"]')
        if normalized_ibs:
            summary, rendered_total = _format_severity_summary(normalized_ibs)
            if summary:
                body_lines.append(f"- **Issues**: {rendered_total} total ({summary})")

    key_patterns_raw = run.get("key_patterns")
    if key_patterns_raw is not None:
        key_patterns = _require_list(key_patterns_raw, "run.key_patterns")
        cleaned_kp = [
            sanitize_one_line(_require_str(p, f"run.key_patterns[{i}]"))
            for i, p in enumerate(key_patterns)
        ]
        cleaned_kp = [p for p in cleaned_kp if p]
        if cleaned_kp:
            body_lines.append(f"- **Key patterns**: {', '.join(cleaned_kp)}")

    specs_raw = run.get("specializations")
    if specs_raw is not None:
        specs = _require_list(specs_raw, "run.specializations")
        cleaned_specs = [
            sanitize_one_line(_require_str(s, f"run.specializations[{i}]"))
            for i, s in enumerate(specs)
        ]
        cleaned_specs = [s for s in cleaned_specs if s]
        if cleaned_specs:
            body_lines.append(f"- **Specializations used**: {', '.join(cleaned_specs)}")

    state["recent_runs"].insert(
        0,
        {"date": date, "description": description, "body_lines": body_lines},
    )

    if len(state["recent_runs"]) > MAX_RECENT_RUNS:
        stats["recent_runs_dropped"] = len(state["recent_runs"]) - MAX_RECENT_RUNS
        del state["recent_runs"][MAX_RECENT_RUNS:]


# ─── File I/O with locking ────────────────────────────────────────────


def _atomic_write(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` atomically, with mode ``FILE_MODE``."""
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp_name, FILE_MODE)
        os.replace(tmp_name, str(path))
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _lock_open_flags() -> int:
    if os.name == "nt":
        return os.O_CREAT | os.O_RDWR
    flags = os.O_CREAT | os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    return flags


def _try_lock(fd: int) -> bool:
    """Non-blocking exclusive lock. True if acquired."""
    if os.name == "nt":
        import msvcrt

        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            return False
    import fcntl

    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False


def _unlock(fd: int) -> None:
    if os.name == "nt":
        import msvcrt

        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        return
    import fcntl

    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass


def _acquire_lock(lock_path: Path) -> int:
    """Acquire an exclusive lock on ``lock_path``. Returns the fd to close.

    Raises ``LockTimeoutError`` on timeout. Raises ``MemoryHelperError``
    if the lock file itself can't be opened.
    """
    try:
        fd = os.open(str(lock_path), _lock_open_flags(), FILE_MODE)
    except OSError as exc:
        raise MemoryHelperError(f"could not open lock file {lock_path}: {exc}")
    try:
        try:
            os.chmod(str(lock_path), FILE_MODE)
        except OSError:
            pass
        deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
        while True:
            if _try_lock(fd):
                return fd
            if time.monotonic() >= deadline:
                raise LockTimeoutError(
                    f"could not acquire lock on {lock_path} within {LOCK_TIMEOUT_SECONDS}s"
                )
            time.sleep(LOCK_POLL_INTERVAL)
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        raise


def _release_lock(fd: int) -> None:
    _unlock(fd)
    try:
        os.close(fd)
    except OSError:
        pass


# ─── Snapshot builder ─────────────────────────────────────────────────


def _build_snapshot(state: dict[str, Any], *, exists: bool) -> dict[str, Any]:
    return {
        "common_issues": [
            {
                "category": cat,
                "description": e["description"],
                "count": e["count"],
            }
            for cat, entries in state["common_issues"].items()
            for e in entries
        ],
        "recent_runs": [
            {
                "date": r["date"],
                "description": r["description"],
                "body_lines": r["body_lines"],
            }
            for r in state["recent_runs"]
        ],
        "exists": exists,
    }


# ─── Block 2: Module Contract ──────────────────────────────────────────

# (Implemented inline in MemoryStore.execute above.)

# ─── Block 3: Module Helpers ───────────────────────────────────────────


def _update(request: MemoryRequest) -> MemoryResult:
    """Merge a JSON spec into the memory file under an exclusive lock."""
    spec = request.spec
    if not spec:
        raise SpecError("update requires a JSON spec")

    paths = memory_paths(create_dir=True)
    file_path = paths["file"]
    lock_path = paths["lock"]

    existed_before = file_path.exists()
    fd = _acquire_lock(lock_path)
    try:
        existing = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
        state = parse_memory_file(existing)
        stats = merge_run(state, spec)
        new_content = render_memory_file(state)
        _atomic_write(file_path, new_content)

        return MemoryResult(
            file=str(file_path),
            existed_before=existed_before,
            stats=stats,
            total_categories=len(
                [c for c, e in state["common_issues"].items() if e]
            ),
            total_patterns=sum(
                len(e) for e in state["common_issues"].values()
            ),
            total_recent_runs=len(state["recent_runs"]),
        )
    finally:
        _release_lock(fd)