"""Tests for CapabilitiesHostSetup.

Covers FRD FR-HOST-001 test cases:
- Setup with origin remote (implement subdir)
- Setup without origin remote (plan subdir)
- Unknown subdir → HostError
- Not inside a git repository → HostError
- Performance: p95 latency < 100ms
- Directory mode 0o700
"""

from __future__ import annotations

import os
import stat
import time

import pytest

from shared.src.common.taxonomy_sdc_constant import (
    SKILL_SUBDIR_EXECUTE,
    SKILL_SUBDIR_IMPLEMENT,
    SKILL_SUBDIR_PLAN,
)
from shared.src.common.taxonomy_sdc_error import HostError
from shared.src.common.taxonomy_sdc_vo import SkillSubdir
from shared.src.host.taxonomy_host_request import HostResult

from host.src.capabilities_host_setup import CapabilitiesHostSetup


# ─── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture()
def setup_cap():
    return CapabilitiesHostSetup()


# ─── FR-HOST-001: Setup with origin remote ───────────────────────────


class TestSetupWithRemote:
    """Inside a git repo with origin remote → directory created."""

    def test_creates_directory_with_remote(
        self, setup_cap, git_repo, develop_root, check_mode
    ):
        result = setup_cap.setup(SkillSubdir(SKILL_SUBDIR_IMPLEMENT))

        assert isinstance(result, HostResult)
        assert result.python  # non-empty
        assert result.run_id  # non-empty
        assert len(result.run_id) == 8

        scratch = develop_root / "my-repo" / SKILL_SUBDIR_IMPLEMENT
        assert scratch.is_dir()
        check_mode(scratch)
        assert result.scratch_dir == str(scratch)

    def test_plan_subdir_with_remote(
        self, setup_cap, git_repo, develop_root, check_mode
    ):
        result = setup_cap.setup(SkillSubdir(SKILL_SUBDIR_PLAN))

        scratch = develop_root / "my-repo" / SKILL_SUBDIR_PLAN
        assert scratch.is_dir()
        check_mode(scratch)
        assert result.scratch_dir == str(scratch)

    def test_execute_subdir_with_remote(
        self, setup_cap, git_repo, develop_root, check_mode
    ):
        result = setup_cap.setup(SkillSubdir(SKILL_SUBDIR_EXECUTE))

        scratch = develop_root / "my-repo" / SKILL_SUBDIR_EXECUTE
        assert scratch.is_dir()
        check_mode(scratch)

    def test_run_id_is_8_hex_chars(self, setup_cap, git_repo, develop_root):
        result = setup_cap.setup(SkillSubdir(SKILL_SUBDIR_IMPLEMENT))

        rid = result.run_id
        assert len(rid) == 8
        int(rid, 16)  # must parse as hex
        assert rid == rid.lower()

    def test_run_id_unique_per_call(self, setup_cap, git_repo, develop_root):
        r1 = setup_cap.setup(SkillSubdir(SKILL_SUBDIR_IMPLEMENT))
        r2 = setup_cap.setup(SkillSubdir(SKILL_SUBDIR_IMPLEMENT))
        assert r1.run_id != r2.run_id

    def test_python_is_absolute_path(self, setup_cap, git_repo, develop_root):
        result = setup_cap.setup(SkillSubdir(SKILL_SUBDIR_IMPLEMENT))
        assert os.path.isabs(result.python)


# ─── FR-HOST-001: Setup without origin remote ────────────────────────


class TestSetupWithoutRemote:
    """Inside a git repo without origin → slug from toplevel dir name."""

    def test_creates_directory_without_remote(
        self, setup_cap, git_repo_no_remote, develop_root, check_mode
    ):
        result = setup_cap.setup(SkillSubdir(SKILL_SUBDIR_PLAN))

        scratch = develop_root / "norepo" / SKILL_SUBDIR_PLAN
        assert scratch.is_dir()
        check_mode(scratch)
        assert result.scratch_dir == str(scratch)


# ─── FR-HOST-001: Unknown subdir ─────────────────────────────────────


class TestSetupUnknownSubdir:
    """Unknown subdir → HostError, no directory created."""

    def test_raises_host_error(self, setup_cap, git_repo, develop_root):
        with pytest.raises(HostError, match="unknown subdir"):
            setup_cap.setup(SkillSubdir("foo"))

    def test_no_directory_created(self, setup_cap, git_repo, develop_root):
        with pytest.raises(HostError):
            setup_cap.setup(SkillSubdir("foo"))

        # No new directories should appear under the repo slug root
        repo_root = develop_root / "my-repo"
        if repo_root.exists():
            assert not (repo_root / "foo").exists()


# ─── FR-HOST-001: Not inside a git repository ────────────────────────


class TestSetupNotInGitRepo:
    """Not inside a git repository → HostError("not inside a git repository")."""

    def test_raises_host_error(
        self, setup_cap, not_a_git_repo, develop_root
    ):
        with pytest.raises(HostError, match="not inside a git repository"):
            setup_cap.setup(SkillSubdir(SKILL_SUBDIR_IMPLEMENT))

    def test_no_directory_created(
        self, setup_cap, not_a_git_repo, develop_root
    ):
        # Record what existed before
        before = set(develop_root.iterdir())

        with pytest.raises(HostError):
            setup_cap.setup(SkillSubdir(SKILL_SUBDIR_IMPLEMENT))

        after = set(develop_root.iterdir())
        assert before == after


# ─── FR-HOST-001: Error message format assertion ────────────────────


class TestSetupErrorMessageFormat:
    """Verify exact error message strings match FRD spec."""

    def test_unknown_subdir_message(self, setup_cap, git_repo):
        with pytest.raises(HostError) as exc_info:
            setup_cap.setup(SkillSubdir("foo"))
        msg = str(exc_info.value)
        assert "host: unknown subdir" in msg
        assert "'foo'" in msg

    def test_not_in_git_repo_message(self, setup_cap, not_a_git_repo):
        with pytest.raises(HostError) as exc_info:
            setup_cap.setup(SkillSubdir(SKILL_SUBDIR_IMPLEMENT))
        assert "not inside a git repository" in str(exc_info.value)


# ─── FR-HOST-001 Metric: Performance (p95 < 100ms) ──────────────────


class TestSetupPerformance:
    """Performance test: setup p95 latency < 100ms."""

    @pytest.mark.skipif(
        os.name != "posix" or __import__("sys").platform != "linux",
        reason="requires Linux (resolve_python checks platform)",
    )
    def test_p95_latency_under_100ms(self, setup_cap, git_repo, develop_root):
        durations: list[float] = []
        n = 1000

        for _ in range(n):
            start = time.perf_counter()
            setup_cap.setup(SkillSubdir(SKILL_SUBDIR_IMPLEMENT))
            elapsed_ms = (time.perf_counter() - start) * 1000
            durations.append(elapsed_ms)

        durations.sort()
        p95_index = int(n * 0.95)
        p95 = durations[p95_index]

        assert p95 < 100.0, (
            f"p95 latency {p95:.2f}ms exceeds 100ms threshold"
        )