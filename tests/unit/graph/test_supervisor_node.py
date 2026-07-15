from __future__ import annotations

from uuid import uuid4

from app.agents.supervisor_agent import SupervisorAgent
from app.graph.nodes.supervisor_node import make_supervisor_node
from app.graph.state import create_initial_state
from app.schemas.routing import NodeName, RoutingDecision
from tests.unit.agents.fakes import FakeStructuredChatModel


async def test_supervisor_node_merges_routing_decision_into_state() -> None:
    decision = RoutingDecision(next_node=NodeName.LEGAL_RESEARCH, reason="research needed")
    llm = FakeStructuredChatModel(responses=[decision])
    agent = SupervisorAgent(llm, model_name="fake-model")
    node = make_supervisor_node(agent)

    state = create_initial_state(uuid4(), uuid4())
    update = await node(state)

    assert update == {"last_routing_decision": decision}


async def test_supervisor_node_binds_agent_name_during_execution() -> None:
    from app.core.logging import current_log_context

    captured: dict[str, object] = {}

    class _CapturingAgent(SupervisorAgent):
        async def run(self, state):
            captured["agent_name_in_context"] = current_log_context().get("agent_name")
            return await super().run(state)

    llm = FakeStructuredChatModel(
        responses=[RoutingDecision(next_node=NodeName.CASE_INTAKE, reason="x")]
    )
    agent = _CapturingAgent(llm, model_name="fake-model")
    node = make_supervisor_node(agent)

    await node(create_initial_state(uuid4(), uuid4()))

    assert captured["agent_name_in_context"] == "supervisor"
