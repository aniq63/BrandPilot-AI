from langgraph.graph import StateGraph, START, END

from src.agents.graph.state import StartupMarketingState
from src.agents.graph.nodes import (
    startup_analysis,
    market_research,
    customer_research,
    social_media_strategy_node,
    strategy_review_node,
    strategy_optimization_node,
    campaign_orchestrator_node,
)
from src.agents.graph.checkpointer import checkpointer


# Initialize graph
workflow = StateGraph(StartupMarketingState)


# Register nodes with correct function names
workflow.add_node(
    "startup_analysis",
    startup_analysis
)

workflow.add_node(
    "market_research",
    market_research
)

workflow.add_node(
    "customer_research",
    customer_research
)

workflow.add_node(
    "social_media_strategy",
    social_media_strategy_node
)

workflow.add_node(
    "strategy_review",
    strategy_review_node,
    destinations={
        "strategy_optimization": "strategy_optimization",
        "campaign_orchestrator": "campaign_orchestrator"
    }
)


workflow.add_node(
    "strategy_optimization",
    strategy_optimization_node
)

workflow.add_node(
    "campaign_orchestrator",
    campaign_orchestrator_node
)


# Initial execution
workflow.add_edge(START, "startup_analysis")


# Run market and customer research in parallel
workflow.add_edge("startup_analysis","market_research")

workflow.add_edge("startup_analysis","customer_research")


# Wait for BOTH research agents to finish
workflow.add_edge(["market_research", "customer_research"],"social_media_strategy")


# Generate strategy and send it for founder review
workflow.add_edge("social_media_strategy","strategy_review")


# After optimization, send the updated strategy back for review
workflow.add_edge("strategy_optimization","strategy_review")


# Campaign execution ends the current workflow
workflow.add_edge("campaign_orchestrator",END)


# Compile with a persistent checkpointer for HITL
app = workflow.compile(
    checkpointer=checkpointer
)
