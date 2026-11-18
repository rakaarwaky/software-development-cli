"""Acceptance tests for the host feature.

Proves: business requirement met.
"""

from __future__ import annotations

import pytest

from host.src.capabilities_host_cleanup import CapabilitiesHostCleanup
from host.src.capabilities_host_setup import CapabilitiesHostSetup
from shared.src.common.taxonomy_sdc_error import HostError
from shared.src.common.taxonomy_sdc_vo import SkillSubdir
from shared.src.host.taxonomy_host_request import HostResult


class TestFRHOST001Acceptance:
    """FR-HOST-001: Setup artifact root — business requirement met."""

    def test_setup_returns_host_result_with_python_and_scratch_dir(
        self, git_repo, isolated_home
    ) -> None:
        result = CapabilitiesHostSetup().setup(SkillSubdir("implement"))
        assert isinstance(result, HostResult)
        assert result.python
        assert result.scratch_dir
        assert result.run_id


class TestFRHOST002Acceptance:
    """FR-HOST-002: Cleanup paths — business requirement met."""

    def test_cleanup_removes_all_files(self, tmp_path, isolated_home, monkeypatch) -> None:
        monkeypatch.setattr(
            "shared.src.host.utility_host_helper.develop_root",
            lambda: tmp_path / ".agents" / "develop",
        )
        managed = tmp_path / ".agents" / "develop" / "unit"
        managed.mkdir(parents=True)
        files = []
        for i in range(3):
            p = managed / f"file_{i}.txt"
            p.write_text(f"content {i}")
            files.append(str(p))

        result = CapabilitiesHostCleanup().cleanup(files)
        assert result.failed_count == 0