"""Contract tests for memory protocols.

Verifies that memory capabilities implement their protocol interfaces:
- IMemoryPathProtocol
- IMemoryReaderProtocol
- IMemorySnapshotProtocol
- IMemoryWriterProtocol
- IMemoryAggregate
"""

from __future__ import annotations

from memory.src.capabilities_memory_path import CapabilitiesPath
from memory.src.capabilities_memory_reader import CapabilitiesReader
from memory.src.capabilities_memory_snapshot import CapabilitiesSnapshot
from memory.src.capabilities_memory_top import CapabilitiesTop
from memory.src.capabilities_memory_writer import CapabilitiesWriter
from shared.src.memory.contract_memory_aggregate import IMemoryAggregate
from shared.src.memory.contract_memory_protocol import (
    IMemoryPathProtocol,
    IMemoryReaderProtocol,
    IMemorySnapshotProtocol,
    IMemoryTopProtocol,
    IMemoryWriterProtocol,
)


class TestIMemoryPathProtocol:
    """IMemoryPathProtocol contract: resolve_paths method exists."""

    def test_capabilities_path_implements_protocol(self) -> None:
        from memory.src.capabilities_memory_path import CapabilitiesPath

        cap = CapabilitiesPath()
        assert isinstance(cap, IMemoryPathProtocol)

    def test_capabilities_path_has_resolve_paths_method(self) -> None:
        from memory.src.capabilities_memory_path import CapabilitiesPath

        cap = CapabilitiesPath()
        assert hasattr(cap, "resolve_paths")
        assert callable(cap.resolve_paths)


class TestIMemoryReaderProtocol:
    """IMemoryReaderProtocol contract: read_content method exists."""

    def test_capabilities_reader_implements_protocol(self) -> None:
        from memory.src.capabilities_memory_reader import CapabilitiesReader

        cap = CapabilitiesReader()
        assert isinstance(cap, IMemoryReaderProtocol)

    def test_capabilities_reader_has_read_content_method(self) -> None:
        from memory.src.capabilities_memory_reader import CapabilitiesReader

        cap = CapabilitiesReader()
        assert hasattr(cap, "read_content")
        assert callable(cap.read_content)


class TestIMemorySnapshotProtocol:
    """IMemorySnapshotProtocol contract: read_snapshot method exists."""

    def test_capabilities_snapshot_implements_protocol(self) -> None:
        from memory.src.capabilities_memory_snapshot import CapabilitiesSnapshot

        cap = CapabilitiesSnapshot()
        assert isinstance(cap, IMemorySnapshotProtocol)

    def test_capabilities_snapshot_has_read_snapshot_method(self) -> None:
        from memory.src.capabilities_memory_snapshot import CapabilitiesSnapshot

        cap = CapabilitiesSnapshot()
        assert hasattr(cap, "read_snapshot")
        assert callable(cap.read_snapshot)


class TestIMemoryWriterProtocol:
    """IMemoryWriterProtocol contract: update method exists."""

    def test_capabilities_writer_implements_protocol(self) -> None:
        cap = CapabilitiesWriter()
        assert isinstance(cap, IMemoryWriterProtocol)

    def test_capabilities_writer_has_update_method(self) -> None:
        cap = CapabilitiesWriter()
        assert hasattr(cap, "update")
        assert callable(cap.update)


class TestIMemoryTopProtocol:
    """IMemoryTopProtocol contract: top method exists."""

    def test_capabilities_top_implements_protocol(self) -> None:
        cap = CapabilitiesTop()
        assert isinstance(cap, IMemoryTopProtocol)

    def test_capabilities_top_has_top_method(self) -> None:
        cap = CapabilitiesTop()
        assert hasattr(cap, "top")
        assert callable(cap.top)


class TestIMemoryAggregate:
    """IMemoryAggregate contract: execute method exists."""

    def test_agent_memory_implements_aggregate(self) -> None:
        from memory.src.agent_memory_orchestrator import AgentMemory

        agent = AgentMemory(
            path_cap=CapabilitiesPath(),
            reader_cap=CapabilitiesReader(),
            snapshot_cap=CapabilitiesSnapshot(),
            writer_cap=CapabilitiesWriter(),
            top_cap=CapabilitiesTop(),
        )
        assert isinstance(agent, IMemoryAggregate)

    def test_agent_memory_has_execute_method(self) -> None:
        from memory.src.agent_memory_orchestrator import AgentMemory

        agent = AgentMemory(
            path_cap=CapabilitiesPath(),
            reader_cap=CapabilitiesReader(),
            snapshot_cap=CapabilitiesSnapshot(),
            writer_cap=CapabilitiesWriter(),
            top_cap=CapabilitiesTop(),
        )
        assert hasattr(agent, "execute")
        assert callable(agent.execute)


class TestRootContainerContract:
    """Root container exposes IMemoryAggregate."""

    def test_create_memory_feature_returns_aggregate(self) -> None:
        from memory.src.root_memory_container import create_memory_feature

        feature = create_memory_feature()
        assert isinstance(feature, IMemoryAggregate)