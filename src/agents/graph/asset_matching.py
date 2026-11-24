import json

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from src.agents.graph.campaign_state import AssetMatchingState
from src.agents.llm.model import asset_matching_model
from src.config.prompts import ASSET_MATCHING_PROMPT
from src.utilis.logging import log_calls


@log_calls
def match_assets(state: AssetMatchingState) -> dict:
    context = {
        "user_id": state["user_id"],
        "project_id": state["project_id"],
        "campaign_id": state["campaign_id"],
    }
    prompt = ASSET_MATCHING_PROMPT.format(
        context=json.dumps(context, indent=2, default=str),
        posts=json.dumps(state["posts"], indent=2, default=str),
        assets=json.dumps(state["assets"], indent=2, default=str),
    )

    content: list[dict] = [{"type": "text", "text": prompt}]
    for asset in state["assets"]:
        if asset.get("file_type") == "image" and asset.get("public_url"):
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": asset["public_url"]},
                }
            )

    result = asset_matching_model.invoke([HumanMessage(content=content)])
    return {"suggestions": result.model_dump()}


graph = StateGraph(AssetMatchingState)
graph.add_node("match_assets", match_assets)
graph.add_edge(START, "match_assets")
graph.add_edge("match_assets", END)

asset_matching_app = graph.compile()
