import json

from langgraph.graph import END, START, StateGraph

from src.agents.graph.campaign_state import CampaignOrchestratorState
from src.agents.llm.model import campaign_plan_model
from src.config.prompts import CAMPAIGN_ORCHESTRATOR_PROMPT
from src.utilis.logging import log_calls


@log_calls
def build_campaign_plan(state: CampaignOrchestratorState) -> dict:
    prompt = CAMPAIGN_ORCHESTRATOR_PROMPT.format(
        context=json.dumps(state["context"], indent=2, default=str)
    )
    plan = campaign_plan_model.invoke(prompt)
    return {"plan": plan.model_dump()}


graph = StateGraph(CampaignOrchestratorState)
graph.add_node("build_campaign_plan", build_campaign_plan)
graph.add_edge(START, "build_campaign_plan")
graph.add_edge("build_campaign_plan", END)

campaign_orchestrator_app = graph.compile()
