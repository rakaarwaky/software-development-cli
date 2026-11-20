"""Integration tests for pool module and DI wiring.

Proves: module / crate / package + DI wiring.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from cli.src.surface_sdc_command import reset_capabilities, set_capabilities
from shared.src.pool.contract_pool_aggregate import IPoolAggregate
from shared.src.pool.taxonomy_pool_request import PoolRequest, PoolResult

from pool.src.agent_pool_orchestrator import AgentPool
from pool.src.capabilities_pool_grok import CapabilitiesPoolGrok


class TestPoolDIWiring:
    """Pool capabilities wired through root container and surface."""

    def test_root_container_wires_all_capabilities(self) -> None:
        from pool.src.root_pool_container import PoolContainer

        container = PoolContainer()
        assert isinstance(container.aggregate, IPoolAggregate)

    def test_root_container_create_pool_feature_is_callable(self) -> None:
        from pool.src.root_pool_container import create_pool_feature

        feature = create_pool_feature()
        assert callable(getattr(feature, "execute", None))

    def test_set_capabilities_accepts_pool_aggregate(self) -> None:
        reset_capabilities()
        pool = AgentPool(grok_cap=CapabilitiesPoolGrok())
        set_capabilities(
            host=MagicMock(),
            memory=MagicMock(),
            planner=MagicMock(),
            pool=pool,
        )
        # pool is wired, so a pool request reaches the capability
        from cli.src.surface_sdc_command import _call_pool

        result = _call_pool(PoolRequest(session_id="t1"))
        assert isinstance(result, PoolResult)
        reset_capabilities()

    def test_pool_not_wired_raises(self) -> None:
        from shared.src.common.taxonomy_sdc_error import PoolNotWiredError

        reset_capabilities()
        # wire only host so pool stays None
        set_capabilities(host=MagicMock(), memory=MagicMock(), planner=MagicMock())
        from cli.src.surface_sdc_command import _call_pool

        try:
            _call_pool(PoolRequest(session_id="t1"))
        except PoolNotWiredError:
            pass
        else:
            raise AssertionError("PoolNotWiredError not raised")
        finally:
            reset_capabilities()
