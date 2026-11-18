"""Host agent orchestrator (AES agent layer).

Routes host requests to the correct per-skill capability. The surface
calls the agent; the agent dispatches to the right capability.
"""

from __future__ import annotations

from shared.src.common.taxonomy_sdc_error import HostError
from shared.src.host.contract_host_protocol import IHostProtocol
from shared.src.host.taxonomy_host_request import HostRequest, HostResult
from host.src.capabilities_host_implement import HostImplement
from host.src.capabilities_host_design import HostDesign
from host.src.capabilities_host_execute import HostExecute


class HostAgent:
    """Agent orchestrator for the host feature.

    Composes the three per-skill capabilities and routes by subdir.
    """

    def __init__(self) -> None:
        self._implement: IHostProtocol = HostImplement()
        self._design: IHostProtocol = HostDesign()
        self._execute: IHostProtocol = HostExecute()

    def dispatch(self, request: HostRequest, *, subdir: str) -> HostResult:
        """Route a host request to the right capability.

        Args:
            request: The host request.
            subdir: One of ``implement``, ``plan``, ``execute``, or ``""``
                (empty string routes cleanup to the implement capability).
        """
        if subdir == "implement":
            return self._implement.execute(request)
        if subdir == "plan":
            return self._design.execute(request)
        if subdir == "execute":
            return self._execute.execute(request)
        return self._implement.execute(request)