"""Integration tests for memory module and DI wiring.

Proves: module / crate / package + DI wiring.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from cli.src.surface_sdc_command import reset_capabilities, set_capabilities
from memory.src.agent_memory_orchestrator import AgentMemory
from memory.src.capabilities_memory_path import CapabilitiesPath
from memory.src.capabilities_memory_reader import CapabilitiesReader
from memory.src.capabilities_memory_top import CapabilitiesTop
from memory.src.capabilities_memory_writer import CapabilitiesWriter
from shared.src.memory.contract_memory_aggregate import IMemoryAggregate


class TestMemoryDIWiring:
    """Memory capabilities wired through root container and surface."""

    def test_root_container_wires_all_capabilities(self) -> None:
        from memory.src.root_memory_container import MemoryContainer

        container = MemoryContainer()
        assert isinstance(container.aggregate, IMemoryAggregate)

    def test_set_capabilities_accepts_memory_aggregate(self) -> None:
        reset_capabilities()
        memory = AgentMemory(
            path_cap=CapabilitiesPath(),
            reader_cap=CapabilitiesReader(),
            writer_cap=CapabilitiesWriter(),
            top_cap=CapabilitiesTop(),
        )
        set_capabilities(
            host=MagicMock(),
            memory=memory,
            planner=MagicMock(),
        )

    def test_root_container_create_memory_feature_is_callable(self) -> None:
        from memory.src.root_memory_container import create_memory_feature

        feature = create_memory_feature()
        assert callable(getattr(feature, "execute", None))


class TestCrossSkillWorkflowPrefixes:
    """All four skills must be able to write memory specs via update."""

    def test_all_four_workflow_prefixes_accepted(self, isolated_home, git_repo) -> None:
        """All four workflow prefixes must be accepted by sdc memory update."""
        writer = CapabilitiesWriter()
        prefixes = ["impl: ", "exec: ", "plan: ", "grill: "]
        for prefix in prefixes:
            res = writer.update({"run": {"description": f"{prefix}test workflow"}})
            # Each should succeed (existed_before may be True after first)
            assert res is not None