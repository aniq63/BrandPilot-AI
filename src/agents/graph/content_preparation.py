import json

from langgraph.graph import END, START, StateGraph

from src.agents.graph.campaign_state import ContentPreparationState
from src.agents.llm.model import content_preparation_model
from src.config.prompts import CONTENT_PREPARATION_PROMPT
from src.utilis.logging import log_calls


@log_calls
def prepare_content(state: ContentPreparationState) -> dict:
    prompt = CONTENT_PREPARATION_PROMPT.format(
        context=json.dumps(
            {
                "user_id": state["user_id"],
                "project_id": state["project_id"],
                "campaign_id": state["campaign_id"],
            },
            indent=2,
        ),
        strategy=json.dumps(state["strategy"], indent=2, default=str),
        posts=json.dumps(state["posts"], indent=2, default=str),
    )
    result = content_preparation_model.invoke(prompt)
    return {"drafts": result.model_dump()}


graph = StateGraph(ContentPreparationState)
graph.add_node("prepare_content", prepare_content)
graph.add_edge(START, "prepare_content")
graph.add_edge("prepare_content", END)

content_preparation_app = graph.compile()
