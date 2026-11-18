"""Planner capability tests.

Covers FR-PLAN-001 (parse), FR-PLAN-002 (validate), and FR-PLAN-003 (compute).
"""

from __future__ import annotations

import sys
from pathlib import Path

# ─── Bootstrap sys.path (mirrors modules/root_sdc_entry.py) ─────────────
_MODULES_ROOT = Path(__file__).resolve().parents[3]
for _m in ("shared", "cli", "planner", "memory", "host"):
    _src = _MODULES_ROOT / "modules" / _m / "src"
    if _src.is_dir():
        _p = str(_src)
        if _p not in sys.path:
            sys.path.insert(0, _p)
# Also add the modules/ root itself so `from modules.shared...` works
if str(_MODULES_ROOT / "modules") not in sys.path:
    sys.path.insert(0, str(_MODULES_ROOT / "modules"))

from shared.src.common.utility_sdc_common import bootstrap_ns_roots

bootstrap_ns_roots()

import pytest  # noqa: E402

from shared.src.common.taxonomy_sdc_error import PlanParseError, PlanUsageError  # noqa: E402
from shared.src.common.taxonomy_sdc_vo import PrEntry  # noqa: E402
from shared.src.planner.taxonomy_planner_request import (  # noqa: E402
    PlanRequest,
    PrEntryList,
)
from planner.src.agent_planner_orchestrator import AgentPlanner  # noqa: E402
from planner.src.capabilities_compute_execution import CapabilitiesComputeExecution  # noqa: E402
from planner.src.capabilities_parse_pr_plan import CapabilitiesParsePrPlan  # noqa: E402
from planner.src.capabilities_validate_dag import CapabilitiesValidateDag  # noqa: E402


# ─── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture()
def parser():
    return CapabilitiesParsePrPlan()


@pytest.fixture()
def validator():
    return CapabilitiesValidateDag()


@pytest.fixture()
def computer():
    return CapabilitiesComputeExecution()


@pytest.fixture()
def orchestrator(parser, validator, computer):
    return AgentPlanner(parser=parser, validator=validator, computer=computer)


# ─── FR-PLAN-001: Parse PR Plan ────────────────────────────────────────

DOC_THREE_VALID = """# Plan Doc

## PR Plan

### PR 0a: Alpha
- Files/components affected: src/a.py
- Dependencies: none
- Description: Alpha PR

### PR 1: Beta
- Files/components affected: src/b.py
- Dependencies: PR 0a
- Description: Beta PR

### PR 2: Gamma
- Files/components affected: src/c.py
- Dependencies: PR 0a, PR 1
- Description: Gamma PR
"""


class TestParseHappyPath:
    """Three valid PR entries → 3 entries with IDs, titles, files, deps, descriptions."""

    def test_returns_three_entries(self, parser):
        result = parser.parse_plan(PrEntryList(text=DOC_THREE_VALID))

        assert result.ok is True
        assert len(result.entries) == 3
        ids = [e.id for e in result.entries]
        assert ids == ["pr-0a", "pr-1", "pr-2"]
        assert result.entries[0].title == "Alpha"
        assert result.entries[0].files == ["src/a.py"]
        assert result.entries[0].dependencies == []
        assert result.entries[0].description == "Alpha PR"
        assert result.entries[1].dependencies == ["pr-0a"]
        assert result.entries[2].dependencies == ["pr-0a", "pr-1"]
        assert result.errors == []


class TestParseMissingSection:
    """No ## PR Plan section → parse error with exit code 4."""

    def test_raises_plan_parse_error_exit_4(self, orchestrator, tmp_path):
        doc = tmp_path / "plan.md"
        doc.write_text("# Doc\n\nNo plan section here.", encoding="utf-8")

        with pytest.raises(PlanParseError) as exc_info:
            orchestrator.execute(PlanRequest(action="validate", path=str(doc)))

        assert exc_info.value.exit_code == 4
        assert "No '## PR Plan' section found in the document" in str(exc_info.value)


class TestParseNoEntries:
    """## PR Plan exists but no entries → parse error with exit code 4."""

    def test_raises_plan_parse_error_exit_4(self, orchestrator, tmp_path):
        doc = tmp_path / "plan.md"
        doc.write_text("# Doc\n\n## PR Plan\n\n", encoding="utf-8")

        with pytest.raises(PlanParseError) as exc_info:
            orchestrator.execute(PlanRequest(action="validate", path=str(doc)))

        assert exc_info.value.exit_code == 4
        assert "No PR entries found in the PR Plan section" in str(exc_info.value)


class TestParseUsageErrors:
    """FRD-PLAN-001: file-not-found and permission errors → PlanUsageError exit 2."""

    def test_file_not_found_exit_2(self, orchestrator, tmp_path):
        missing = tmp_path / "does_not_exist.md"
        with pytest.raises(PlanUsageError) as exc_info:
            orchestrator.execute(PlanRequest(action="validate", path=str(missing)))

        assert exc_info.value.exit_code == 2
        assert "File not found" in str(exc_info.value)

    def test_permission_error_exit_2(self, orchestrator, tmp_path):
        doc = tmp_path / "noread.md"
        doc.write_text("## PR Plan\n\n### PR 1: X\n- Description: x\n", encoding="utf-8")
        doc.chmod(0o000)
        try:
            with pytest.raises(PlanUsageError) as exc_info:
                orchestrator.execute(PlanRequest(action="validate", path=str(doc)))
            assert exc_info.value.exit_code == 2
        finally:
            doc.chmod(0o644)


class TestParseBadDependencyFormat:
    """Unrecognized dependency format → error recorded, other entries still parsed."""

    def test_continues_parsing_other_entries(self, parser):
        doc = """## PR Plan

### PR 1: Good
- Dependencies: bad-format, PR 2
- Description: Good entry

### PR 2: Also Good
- Dependencies: none
- Description: Another entry
"""
        result = parser.parse_plan(PrEntryList(text=doc))

        assert result.ok is False
        assert result.entries == []
        assert any("Unrecognized dependency format" in e for e in result.errors)
        assert any("bad-format" in e for e in result.errors)


class TestParseFencedCodeBlocks:
    """Fenced code blocks (``` / ~~~) are stripped so headings inside are ignored."""

    def test_heading_inside_backtick_fenced_block_ignored(self, parser):
        doc = """## PR Plan

### PR 1: Real Entry
- Dependencies: none
- Description: A real entry

```
### PR 2: Fake Entry
- Dependencies: none
- Description: Should be ignored
```

### PR 3: Another Real Entry
- Dependencies: PR 1
- Description: Yet another real entry
"""
        result = parser.parse_plan(PrEntryList(text=doc))

        assert result.ok is True
        assert len(result.entries) == 2
        ids = [e.id for e in result.entries]
        assert ids == ["pr-1", "pr-3"]

    def test_heading_inside_tilde_fenced_block_with_info_string_ignored(self, parser):
        doc = """## PR Plan

### PR 1: Real Entry
- Dependencies: none
- Description: Real

~~~markdown
### PR 99: Fake Entry
- Dependencies: none
- Description: Fake
~~~

### PR 2: Another Real Entry
- Dependencies: PR 1
- Description: Real
"""
        result = parser.parse_plan(PrEntryList(text=doc))

        assert result.ok is True
        assert [e.id for e in result.entries] == ["pr-1", "pr-2"]


class TestParseRejectsMalformedHeadingsAndDependencies:
    def test_no_title_is_parse_error(self, parser):
        doc = """## PR Plan

### PR 1:
- Files/components affected: src/a.py
- Dependencies: none
- Description: Missing title
"""
        result = parser.parse_plan(PrEntryList(text=doc))

        assert result.ok is False
        assert any("missing a title" in e for e in result.errors)

    def test_dependencies_require_full_match(self, parser):
        doc = """## PR Plan

### PR 1: First
- Files/components affected: src/a.py
- Dependencies: none
- Description: First

### PR 2: Second
- Files/components affected: src/b.py
- Dependencies: PR 1 and PR 3
- Description: Second
"""
        result = parser.parse_plan(PrEntryList(text=doc))

        assert result.ok is False
        assert any("Unrecognized dependency format" in e for e in result.errors)

    def test_empty_dependency_does_not_absorb_next_bullet(self, parser):
        doc = """## PR Plan

### PR 1: First
- Files/components affected: src/a.py
- Dependencies:
- Description: Should remain separate
"""
        result = parser.parse_plan(PrEntryList(text=doc))

        assert result.ok is True
        assert result.entries[0].dependencies == []
        assert result.entries[0].description == "Should remain separate"
        assert result.errors == []

    def test_indented_sibling_bullets_do_not_absorb_fields(self, parser):
        doc = """## PR Plan

### PR 1: First
  - Files/components affected: src/a.py
  - Dependencies: none
  - Description: Separate bullets
"""
        result = parser.parse_plan(PrEntryList(text=doc))

        assert result.ok is True
        assert result.entries[0].dependencies == []
        assert result.entries[0].description == "Separate bullets"


# ─── Surface integration: PlanParseError reaches cmd_sdc with exit 4 ───


class TestSurfaceParseErrorExit4:
    """End-to-end: missing section / no entries → cmd_sdc exit code 4."""

    def _wire(self, monkeypatch, parser=None, validator=None, computer=None):
        """Wire real planner capabilities into the CLI surface."""
        from cli.src.surface_sdc_command import reset_capabilities, set_capabilities
        reset_capabilities()
        set_capabilities(
            host=__import__("unittest.mock", fromlist=["MagicMock"]).MagicMock(),
            memory=__import__("unittest.mock", fromlist=["MagicMock"]).MagicMock(),
            planner=AgentPlanner(
                parser=parser or CapabilitiesParsePrPlan(),
                validator=validator or CapabilitiesValidateDag(),
                computer=computer or CapabilitiesComputeExecution(),
            ),
        )

    def test_missing_section_exit_4(self, monkeypatch, tmp_path):
        self._wire(monkeypatch)
        from cli.src.surface_sdc_command import cmd_sdc

        doc = tmp_path / "plan.md"
        doc.write_text("# Doc\n\nNo plan section here.", encoding="utf-8")

        out, err = self._run(cmd_sdc, ["validate-plan", str(doc)])

        err_text = err.getvalue()
        assert err_text != ""
        assert "No '## PR Plan' section found" in err_text

    def test_no_entries_exit_4(self, monkeypatch, tmp_path):
        self._wire(monkeypatch)
        from cli.src.surface_sdc_command import cmd_sdc

        doc = tmp_path / "plan.md"
        doc.write_text("# Doc\n\n## PR Plan\n\n", encoding="utf-8")

        out, err = self._run(cmd_sdc, ["validate-plan", str(doc)])

        err_text = err.getvalue()
        assert err_text != ""
        assert "No PR entries found" in err_text

    @staticmethod
    def _run(fn, argv):
        import sys
        from io import StringIO

        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err = StringIO(), StringIO()
        try:
            code = fn(argv)
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        return out, err


# ─── FR-PLAN-002: Validate DAG ─────────────────────────────────────────


def _entry(pid: str, deps: list[str] | None = None, **kw) -> PrEntry:
    return PrEntry(
        id=pid,
        number=pid.split("-", 1)[1] if "-" in pid else pid,
        title=kw.get("title", pid),
        files=kw.get("files", []),
        dependencies=deps or [],
        description=kw.get("description", ""),
    )


class TestValidateDuplicateId:
    """Two PR entries share the same ID → Duplicate PR ID error."""

    def test_reports_duplicate_id(self, validator):
        entries = PrEntryList(
            entries=[_entry("pr-1"), _entry("pr-1", title="dup")]
        )
        result = validator.validate_dag(entries)

        assert result.ok is False
        assert any("Duplicate PR ID: 'pr-1'" in e for e in result.errors)


class TestValidateMissingDependency:
    """Entry depends on non-existent PR → error referencing that PR."""

    def test_reports_missing_dependency(self, validator):
        entries = PrEntryList(entries=[_entry("pr-a", deps=["pr-99"])])
        result = validator.validate_dag(entries)

        assert result.ok is False
        assert len(result.errors) == 1
        assert "PR 99" in result.errors[0] and "PR a" in result.errors[0]


class TestValidateCycle:
    """A → B → A → Cycle detected error."""

    def test_reports_cycle(self, validator):
        entries = PrEntryList(
            entries=[
                _entry("pr-a", deps=["pr-b"]),
                _entry("pr-b", deps=["pr-a"]),
            ]
        )
        result = validator.validate_dag(entries)

        assert result.ok is False
        assert any("Cycle detected" in e for e in result.errors)


class TestValidateValidDag:
    """All dependencies valid and acyclic → empty error list."""

    def test_returns_empty_errors(self, validator):
        entries = PrEntryList(
            entries=[
                _entry("pr-a"),
                _entry("pr-b", deps=["pr-a"]),
                _entry("pr-c", deps=["pr-a", "pr-b"]),
            ]
        )
        result = validator.validate_dag(entries)

        assert result.ok is True
        assert result.errors == []


# ─── FR-PLAN-003: Compute Execution Plan ───────────────────────────────


class TestComputeChain:
    """A → B → C chain → levels 0, 1, 2; max parallelism 1."""

    def test_chain_levels_and_parallelism(self, computer):
        entries = PrEntryList(
            entries=[
                _entry("pr-a"),
                _entry("pr-b", deps=["pr-a"]),
                _entry("pr-c", deps=["pr-b"]),
            ]
        )
        result = computer.compute_levels(entries)

        assert result.ok is True
        assert result.levels == 3
        assert result.max_parallelism == 1
        assert result.level_assignments == {"pr-a": 0, "pr-b": 1, "pr-c": 2}
        assert result.linearized_order == ["pr-a", "pr-b", "pr-c"]


class TestComputeIndependent:
    """All independent → all level 0; max parallelism = count; numeric sort."""

    def test_independent_levels_and_order(self, computer):
        entries = PrEntryList(
            entries=[
                _entry("pr-10"),
                _entry("pr-2"),
                _entry("pr-1"),
            ]
        )
        result = computer.compute_levels(entries)

        assert result.ok is True
        assert result.levels == 1
        assert result.max_parallelism == 3
        assert result.level_assignments == {"pr-1": 0, "pr-2": 0, "pr-10": 0}
        assert result.linearized_order == ["pr-1", "pr-2", "pr-10"]


class TestComputeForkDiamond:
    """Two roots at level 0 and one dependent at level 1 → max_parallelism 2."""

    def test_fork_diamond_parallelism(self, computer):
        entries = PrEntryList(
            entries=[
                _entry("pr-a"),
                _entry("pr-b"),
                _entry("pr-c", deps=["pr-a", "pr-b"]),
            ]
        )
        result = computer.compute_levels(entries)

        assert result.ok is True
        assert result.levels == 2
        assert result.max_parallelism == 2
        assert result.level_assignments == {"pr-a": 0, "pr-b": 0, "pr-c": 1}
        assert result.linearized_order == ["pr-a", "pr-b", "pr-c"]


class TestComputeEmpty:
    """No entries → levels=0, max_parallelism=0, empty order."""

    def test_empty_returns_zeros(self, computer):
        result = computer.compute_levels(PrEntryList(entries=[]))

        assert result.ok is True
        assert result.levels == 0
        assert result.max_parallelism == 0
        assert result.linearized_order == []
        assert result.level_assignments == {}


class TestComputeMixedIdOrdering:
    """Same level, mixed numeric/alpha IDs → numeric first, then lexicographic."""

    def test_numeric_then_lexicographic(self, computer):
        entries = PrEntryList(
            entries=[
                _entry("pr-z"),
                _entry("pr-10"),
                _entry("pr-2"),
                _entry("pr-1"),
            ]
        )
        result = computer.compute_levels(entries)

        assert result.ok is True
        assert result.levels == 1
        assert result.max_parallelism == 4
        assert result.linearized_order == ["pr-1", "pr-2", "pr-10", "pr-z"]
