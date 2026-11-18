"""Memory helper shared utility (AES utility layer).

Stateless helpers shared across the memory capabilities and agent:
pure markdown parsing, rendering, lock helpers, and atomic file write.
No class definitions, no state — pure module-level functions only (AES404).
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import time
from collections import OrderedDict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shared.src.common.taxonomy_sdc_constant import (
    CATEGORY_RE,
    DEFAULT_HEADER,
    FILE_MODE,
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


def get_workspace_id() -> str:
    """Return ``"<readable-name>-<hash12>"`` identifying this workspace."""
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
    raw_name = raw_name.removesuffix(".git")
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in raw_name)
    safe_name = safe_name.strip("_.-")[:40].rstrip("_.-") or "workspace"

    return f"{safe_name}-{digest}"


def memory_paths(*, create_dir: bool = False) -> dict[str, Path]:
    """Return ``{"dir", "file", "lock"}`` for this repo."""
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


def parse_memory_file(content: str) -> dict[str, Any]:
    """Parse the memory file into a structured dict."""
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

    state["header"] = drop_trailing_blank(state["header"])
    for run in state["recent_runs"]:
        run["body_lines"] = drop_trailing_blank(run["body_lines"])
    return state


def drop_trailing_blank(lines: list[str]) -> list[str]:
    """Return a new list with trailing blank/whitespace-only lines removed."""
    end = len(lines)
    while end > 0 and not lines[end - 1].strip():
        end -= 1
    return list(lines[:end])


def render_memory_file(state: dict[str, Any]) -> str:
    """Render the parsed state back to markdown."""
    out: list[str] = []

    header = state.get("header") or list(DEFAULT_HEADER)
    out.extend(drop_trailing_blank(header))
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
        out.extend(drop_trailing_blank(run.get("body_lines") or []))
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def format_severity_summary(ibs: dict[str, int]) -> tuple[str, int]:
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


def bump_or_append(
    entries: list[dict[str, Any]],
    lookup: dict[str, dict[str, Any]],
    description: str,
) -> bool:
    """Increment matching entry's count, or append a new one."""
    norm_new = normalize(description)
    match = lookup.get(norm_new)
    if match is not None:
        match["count"] += 1
        return True
    new_entry = {"description": description, "count": 1}
    entries.append(new_entry)
    lookup[norm_new] = new_entry
    return False


def canonical_category(existing: Any, name: str) -> str:
    """Return the existing category matching ``name`` ignoring case/whitespace."""
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
        if not isinstance(patterns, list):
            raise SpecError('"patterns" must be a list')
        for idx, raw in enumerate(patterns):
            if not isinstance(raw, dict):
                raise SpecError(f'"patterns[{idx}]" must be an object')

            category_raw = raw.get("category")
            if category_raw is None or category_raw == "":
                category = "Other"
            else:
                if not isinstance(category_raw, str):
                    raise SpecError(f'"patterns[{idx}].category" must be a string')
                category = sanitize_one_line(category_raw) or "Other"

            desc_raw = raw.get("description")
            if desc_raw is not None and not isinstance(desc_raw, str):
                raise SpecError(f'"patterns[{idx}].description" must be a string')
            description = sanitize_one_line(desc_raw or "")
            if not description:
                continue

            category = canonical_category(state["common_issues"], category)
            entries = state["common_issues"].setdefault(category, [])
            lookup = category_lookups.get(category)
            if lookup is None:
                lookup = {normalize(e["description"]): e for e in entries}
                category_lookups[category] = lookup
            if bump_or_append(entries, lookup, description):
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
        if not isinstance(run_raw, dict):
            raise SpecError('"run" must be an object')
        if run_raw:
            merge_recent_run(state, run_raw, stats)

    stats["categories_touched"] = sorted(touched)
    return stats


def merge_recent_run(state: dict[str, Any], run: dict[str, Any], stats: dict[str, Any]) -> None:
    """Validate and prepend a Recent Runs entry. Updates ``stats`` in place."""
    date_raw = run.get("date")
    if date_raw is None or (isinstance(date_raw, str) and not date_raw.strip()):
        date = datetime.now(UTC).strftime("%Y-%m-%d")
    else:
        if not isinstance(date_raw, str):
            raise SpecError('"run.date" must be a string')
        date_str = date_raw.strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise SpecError(
                f'"run.date" must be a calendar-valid YYYY-MM-DD date, got {date_str!r}'
            )
        date = date_str

    desc_raw = run.get("description")
    if desc_raw is not None and not isinstance(desc_raw, str):
        raise SpecError('"run.description" must be a string')
    description = sanitize_one_line(desc_raw or "") or "(no description)"
    description = description.replace('"', "").strip() or "(no description)"
    description = f'"{description}"'

    body_lines: list[str] = []

    rounds_raw = run.get("rounds")
    if rounds_raw is not None:
        if isinstance(rounds_raw, bool) or not isinstance(rounds_raw, int):
            raise SpecError('"run.rounds" must be an integer')
        body_lines.append(f"- **Rounds**: {rounds_raw}")

    ibs_raw = run.get("issues_by_severity")
    if ibs_raw is not None:
        if not isinstance(ibs_raw, dict):
            raise SpecError('"run.issues_by_severity" must be an object')
        normalized_ibs: dict[str, int] = {}
        for sev, count in ibs_raw.items():
            if not isinstance(sev, str):
                raise SpecError('"run.issues_by_severity" keys must be strings')
            if isinstance(count, bool) or not isinstance(count, int):
                raise SpecError(f'run.issues_by_severity["{sev}"] must be an integer')
            normalized_ibs[sev] = count
        if normalized_ibs:
            summary, rendered_total = format_severity_summary(normalized_ibs)
            if summary:
                body_lines.append(f"- **Issues**: {rendered_total} total ({summary})")

    key_patterns_raw = run.get("key_patterns")
    if key_patterns_raw is not None:
        if not isinstance(key_patterns_raw, list):
            raise SpecError('"run.key_patterns" must be a list')
        cleaned_kp = []
        for i, p in enumerate(key_patterns_raw):
            if not isinstance(p, str):
                raise SpecError(f'"run.key_patterns[{i}]" must be a string')
            cleaned_kp.append(sanitize_one_line(p))
        cleaned_kp = [p for p in cleaned_kp if p]
        if cleaned_kp:
            body_lines.append(f"- **Key patterns**: {', '.join(cleaned_kp)}")

    specs_raw = run.get("specializations")
    if specs_raw is not None:
        if not isinstance(specs_raw, list):
            raise SpecError('"run.specializations" must be a list')
        cleaned_specs = []
        for i, s in enumerate(specs_raw):
            if not isinstance(s, str):
                raise SpecError(f'"run.specializations[{i}]" must be a string')
            cleaned_specs.append(sanitize_one_line(s))
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


def atomic_write(path: Path, content: str) -> None:
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


def acquire_lock(lock_path: Path) -> int:
    """Acquire exclusive lock on ``lock_path``."""
    import fcntl

    flags = os.O_CREAT | os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    try:
        fd = os.open(str(lock_path), flags, FILE_MODE)
    except OSError as exc:
        raise MemoryHelperError(f"could not open lock file {lock_path}: {exc}")
    try:
        try:
            os.chmod(str(lock_path), FILE_MODE)
        except OSError:
            pass
        deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return fd
            except BlockingIOError:
                pass
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


def release_lock(fd: int) -> None:
    """Release exclusive lock."""
    import fcntl

    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass
    try:
        os.close(fd)
    except OSError:
        pass


def build_snapshot_payload(state: dict[str, Any], *, exists: bool) -> dict[str, Any]:
    """Build JSON snapshot dict from parsed state."""
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
