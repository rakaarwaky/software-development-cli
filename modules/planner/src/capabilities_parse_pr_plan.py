"""PR Plan parser capability (AES capabilities layer, capability 1/3).

Implements IPlanParseProtocol: extracts PR entries from the ## PR Plan
section of a plan document.
"""

from __future__ import annotations

import re

from shared.src.common.taxonomy_sdc_vo import PrEntry
from shared.src.planner.contract_planner_protocol import IPlanParseProtocol
from shared.src.planner.taxonomy_planner_request import ParseResult, PrEntryList

# ─── Block 1: Module Declaration ──────────────────────────────────────

class CapabilitiesParsePrPlan(IPlanParseProtocol):
    """Capability: parse the ``## PR Plan`` section of a plan document."""

    def __init__(self) -> None:
        pass

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def parse_plan(self, plan_text: PrEntryList) -> ParseResult:
        """Parse ``plan_text`` into PR entries.

        Returns ``ok=True`` with the parsed entries; non-fatal dependency
        format errors are collected alongside valid entries in ``errors``.
        Returns ``ok=False`` with errors only when the document lacks a
        ``## PR Plan`` section or contains no PR entries.
        """
        text = plan_text.text
        stripped = _strip_fenced_code_blocks(text)
        heading = re.search(r"^## PR Plan[ \t]*$", stripped, re.MULTILINE | re.IGNORECASE)
        if heading is None:
            return ParseResult(
                ok=False,
                errors=["No '## PR Plan' section found in the document"],
            )

        start = heading.end()
        next_section = re.search(
            r"^## (?!PR Plan[ \t]*$)", stripped[start:], re.MULTILINE | re.IGNORECASE
        )
        section = (
            stripped[start : start + next_section.start()]
            if next_section
            else stripped[start:]
        )

        pr_re = re.compile(r"^###[ \t]+PR[ \t]+(\S+?):[ \t]*(.*)$", re.MULTILINE)
        matches = list(pr_re.finditer(section))

        if not matches:
            return ParseResult(
                ok=False,
                errors=["No PR entries found in the PR Plan section"],
            )

        entries: list[PrEntry] = []
        parse_errors: list[str] = []
        for i, m in enumerate(matches):
            pr_num = m.group(1)
            title = m.group(2).strip()
            if not title:
                parse_errors.append(f"PR {pr_num} heading is missing a title")
                continue

            body_start = m.end()
            body_end = (
                matches[i + 1].start() if i + 1 < len(matches) else len(section)
            )
            body = section[body_start:body_end]

            files_raw = _extract_field(body, "Files/components affected")
            deps_raw = _extract_field(body, "Dependencies")
            description = _extract_field(body, "Description") or ""

            files = (
                [f.strip() for f in files_raw.split(",") if f.strip()]
                if files_raw
                else []
            )
            dependencies, dep_errors = _parse_dependencies(deps_raw, f"PR {pr_num}")
            parse_errors.extend(dep_errors)

            entries.append(
                PrEntry(
                    id=f"pr-{pr_num.lower()}",
                    number=pr_num,
                    title=title,
                    files=files,
                    dependencies=dependencies,
                    description=description,
                )
            )

        if parse_errors:
            return ParseResult(ok=False, entries=[], errors=parse_errors)
        return ParseResult(ok=True, entries=entries)

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    def __repr__(self) -> str:
        return "CapabilitiesParsePrPlan()"


def _strip_fenced_code_blocks(content: str) -> str:
    """Remove fenced code blocks so headings inside examples are ignored."""
    flags = re.MULTILINE | re.DOTALL
    content = re.sub(r"^[ \t]*```[^\n]*\n.*?^[ \t]*```[ \t]*$", "", content, flags=flags)
    return re.sub(r"^[ \t]*~~~[^\n]*\n.*?^[ \t]*~~~[ \t]*$", "", content, flags=flags)


def _slugify_title(title: str) -> str:
    """Return a conservative branch-name slug for a PR title."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)[:50].rstrip("-")
    slug = slug.removesuffix(".lock")
    return slug or "unnamed"


def _extract_field(body: str, field_name: str) -> str | None:
    """Return the value of a ``- **FieldName:** value`` bullet, or None."""
    escaped = re.escape(field_name)
    pattern = re.compile(
        rf"^[ \t]*[-*][ \t]+\**{escaped}:?[ \t]*\**:?[ \t]*(.*)$",
        re.MULTILINE | re.IGNORECASE,
    )
    m = pattern.search(body)
    if m:
        return re.sub(r"[ \t]*\n[ \t]+", " ", m.group(1)).strip()
    return None


def _parse_dependencies(
    deps_raw: str | None, pr_label: str
) -> tuple[list[str], list[str]]:
    """Turn a dependency string like ``"PR 0a, PR 1"`` into ``(ids, errors)``."""
    if not deps_raw:
        return [], []
    stripped = deps_raw.strip()
    if stripped.lower() in ("none", "n/a", "-", ""):
        return [], []

    parts = [p.strip() for p in stripped.split(",")]
    deps: list[str] = []
    errors: list[str] = []
    for part in parts:
        if not part:
            continue
        m = re.fullmatch(r"PR[ \t]+([A-Za-z0-9]+)[ \t]*[.,;]?", part, re.IGNORECASE)
        if m:
            deps.append(f"pr-{m.group(1).lower()}")
        else:
            errors.append(
                f"Unrecognized dependency format '{part}' in {pr_label} "
                f"(expected 'PR <id>')"
            )
    return deps, errors