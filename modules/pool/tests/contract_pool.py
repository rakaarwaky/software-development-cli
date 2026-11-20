"""Contract tests for pool protocols.

Verifies that:
- CapabilitiesPoolGrok implements IPoolGrokProtocol (has poll).
- AgentPool implements IPoolAggregate (has execute).
- Root container returns IPoolAggregate.
"""

from __future__ import annotations

from shared.src.pool.contract_pool_aggregate import IPoolAggregate
from shared.src.pool.contract_pool_protocol import IPoolGrokProtocol


class TestIPoolGrokProtocol:
    """IPoolGrokProtocol contract: poll method exists."""

    def test_capabilities_pool_grok_implements_protocol(self) -> None:
        from pool.src.capabilities_pool_grok import CapabilitiesPoolGrok

        cap = CapabilitiesPoolGrok()
        assert isinstance(cap, IPoolGrokProtocol)

    def test_capabilities_pool_grok_has_poll_method(self) -> None:
        from pool.src.capabilities_pool_grok import CapabilitiesPoolGrok

        cap = CapabilitiesPoolGrok()
        assert hasattr(cap, "poll")
        assert callable(cap.poll)


class TestIPoolAggregate:
    """IPoolAggregate contract: execute method exists."""

    def test_agent_pool_implements_aggregate(self) -> None:
        from pool.src.agent_pool_orchestrator import AgentPool
        from pool.src.capabilities_pool_grok import CapabilitiesPoolGrok

        agent = AgentPool(grok_cap=CapabilitiesPoolGrok())
        assert isinstance(agent, IPoolAggregate)

    def test_agent_pool_has_execute_method(self) -> None:
        from pool.src.agent_pool_orchestrator import AgentPool
        from pool.src.capabilities_pool_grok import CapabilitiesPoolGrok

        agent = AgentPool(grok_cap=CapabilitiesPoolGrok())
        assert hasattr(agent, "execute")
        assert callable(agent.execute)


class TestRootContainerContract:
    """Root container exposes IPoolAggregate."""

    def test_create_pool_feature_returns_aggregate(self) -> None:
        from pool.src.root_pool_container import create_pool_feature

        feature = create_pool_feature()
        assert isinstance(feature, IPoolAggregate)
