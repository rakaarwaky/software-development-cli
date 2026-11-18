"""Memory composition root — wires four capabilities into AgentMemory."""

from __future__ import annotations

from modules.memory.src.agent_memory_orchestrator import AgentMemory
from modules.memory.src.capabilities_memory_path import CapabilitiesPath
from modules.memory.src.capabilities_memory_reader import CapabilitiesReader
from modules.memory.src.capabilities_memory_snapshot import CapabilitiesSnapshot
from modules.memory.src.capabilities_memory_writer import CapabilitiesWriter
from shared.src.memory.contract_memory_aggregate import IMemoryAggregate


class MemoryContainer:
    """Construct the memory capabilities and orchestrator (wiring only)."""

    def __init__(self) -> None:
        self._orchestrator = AgentMemory(
            path_cap=CapabilitiesPath(),
            reader_cap=CapabilitiesReader(),
            snapshot_cap=CapabilitiesSnapshot(),
            writer_cap=CapabilitiesWriter(),
        )

    @property
    def aggregate(self) -> IMemoryAggregate:
        return self._orchestrator


def create_memory_feature() -> IMemoryAggregate:
    """Fully-wired memory feature aggregate (factory for entry / DI)."""
    return MemoryContainer().aggregate
