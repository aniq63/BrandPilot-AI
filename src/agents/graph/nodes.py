import json

from src.agents.llm.model import(
    startup_analysis_llm,
    social_media_strategy_model,
    strategy_optimization_model,
    market_research_llm,
    customer_research_llm
)

from src.services.campaign_service import start_campaign_orchestration

from src.agents.graph.state import StartupMarketingState
from src.utilis.web_research import perform_web_research
from src.utilis.extract_url_info import extract_startup_info
from src.utilis.logging import logger, log_calls

from src.config.prompts import (
    STARTUP_ANALYSIS_PROMPT,
    MARKET_RESEARCH_PROMPT,
    CUSTOMER_RESEARCH_PROMPT,
    SOCIAL_MEDIA_STRATEGY_PROMPT,
    STRATEGY_OPTIMIZATION_PROMPT
)


def _response_text(response) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                else:
                    parts.append(json.dumps(item, ensure_ascii=False))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    if isinstance(content, dict):
        text = content.get("text")
        return text if isinstance(text, str) else json.dumps(content, ensure_ascii=False)
    return str(content)


# ============================= STARTUP ANALYSIS NODE =============================

@log_calls
def startup_analysis(state: StartupMarketingState) -> dict:

    # Step 1: Extract information from the startup website
    web_info = extract_startup_info(state["website_url"])

    # Step 2: Prepare the startup information
    startup_context = {
        "startup_name": state["startup_name"],
        "website_url": state["website_url"],
        "product_name": state["product_name"],
        "product_description": state["product_description"],
        "industry": state["industry"],
        "product_pricing": state.get("product_pricing"),
        "main_competitors": state.get("main_competitors"),
        "ideal_customers": state.get("ideal_customers"),
        "target_market": state.get("target_market"),
        "customer_pain_points": state.get("customer_pain_points"),
        "existing_customer_base": state.get("existing_customer_base"),
        "marketing_goals": state.get("marketing_goals", [])
    }

    # Step 3: Create the analysis prompt
    prompt = STARTUP_ANALYSIS_PROMPT.format(
        startup_context=startup_context,
        web_info=web_info
    )

    # Step 4: Generate the startup analysis
    response = startup_analysis_llm.invoke(prompt)

    # Step 5: Return the analysis to LangGraph state
    return {
        "agent_startup_analysis": _response_text(response)
    }


# ============================= MARKET RESEARCH NODE =============================
@log_calls
def market_research(state: StartupMarketingState) -> dict:

    # 1. Collect startup context
    startup_context = {
        "startup_name": state.get("startup_name"),
        "product_name": state.get("product_name"),
        "product_description": state.get("product_description"),
        "industry": state.get("industry"),
        "product_pricing": state.get("product_pricing"),
        "main_competitors": state.get("main_competitors"),
        "target_market": state.get("target_market"),
        "marketing_goals": state.get("marketing_goals"),
        "startup_analysis": state.get("agent_startup_analysis")
    }

    # 2. Define targeted research queries
    search_queries = [
        f"Current industry trends, market demand, and growth in {startup_context['industry']}",

        f"Market size, growth forecasts, and opportunities in {startup_context['industry']}",

        f"Major direct and indirect competitors of {startup_context['product_name']} in {startup_context['industry']}",

        f"Competitor products, pricing models, positioning, strengths and weaknesses in {startup_context['industry']}",

        f"Emerging opportunities, threats, and industry developments in {startup_context['industry']}"
    ]

    # Include known competitors in the search
    if startup_context["main_competitors"]:
        search_queries.append(
            f"Detailed competitive analysis of "
            f"{', '.join(startup_context['main_competitors'])}"
        )

    # 3. Conduct web research
    web_research = perform_web_research(search_queries)

    # 4. Prepare professional research prompt
    prompt = MARKET_RESEARCH_PROMPT.format(
        startup_context=startup_context,
        web_research=web_research
    )

    # 5. Generate research report
    response = market_research_llm.invoke(prompt)

    # 6. Update graph state
    return {
        "agent_market_research": _response_text(response)
    }


# ============================= CUSTOMER RESEARCH NODE =============================
@log_calls
def customer_research(state: StartupMarketingState) -> dict:

    # 1. Collect startup context
    startup_context = {
        "startup_name": state.get("startup_name"),
        "product_name": state.get("product_name"),
        "product_description": state.get("product_description"),
        "industry": state.get("industry"),
        "ideal_customers": state.get("ideal_customers"),
        "target_market": state.get("target_market"),
        "customer_pain_points": state.get("customer_pain_points"),
        "existing_customer_base": state.get("existing_customer_base"),
        "product_pricing": state.get("product_pricing"),
        "marketing_goals": state.get("marketing_goals"),
        "startup_analysis": state.get("agent_startup_analysis")
    }

    # 2. Define targeted research queries
    search_queries = [
        f"Target customer segments, needs, and buying behavior in {startup_context['industry']}",

        f"Common customer pain points and challenges related to {startup_context['product_name']}",

        f"Customer reviews and user feedback about products similar to {startup_context['product_name']}",

        f"How customers evaluate, compare, and purchase solutions in {startup_context['industry']}",

        f"Customer objections, adoption barriers, and reasons for switching products in {startup_context['industry']}",

        f"Where target customers discover and research products in {startup_context['industry']}"
    ]

    # 3. Conduct web research
    web_research = perform_web_research(search_queries)

    # 4. Prepare professional research prompt
    prompt = CUSTOMER_RESEARCH_PROMPT.format(
        startup_context=startup_context,
        web_research=web_research
    )
    # 4. Generate research report
    response = customer_research_llm.invoke(prompt)

    # 5. Update graph state
    return {
        "agent_customer_research": _response_text(response)
    }

# ============================= SOCIAL MEDIA STARTEGIST NODE =============================


@log_calls
def social_media_strategy_node(state: StartupMarketingState):

    logger.info("Generating social media marketing strategy")

    research_context = {
        "startup_information": {
            "startup_name": state.get("startup_name"),
            "product_name": state.get("product_name"),
            "product_description": state.get("product_description"),
            "industry": state.get("industry"),
            "product_pricing": state.get("product_pricing"),
            "website_url": state.get("website_url")
        },

        "marketing_goals": state.get("marketing_goals"),

        "marketing_resources": {
            "brand_tone": state.get("brand_tone"),
            "brand_identity": state.get("brand_identity"),
            "campaign_duration": state.get("campaign_duration"),
            "social_media_accounts": state.get("social_media_accounts"),
            "brand_assets": state.get("brand_assets")
        },

        "startup_analysis": state.get("agent_startup_analysis"),

        "market_research": state.get("agent_market_research"),

        "customer_research": state.get("agent_customer_research")
    }

    prompt = SOCIAL_MEDIA_STRATEGY_PROMPT.format(
        context=json.dumps(research_context, indent=2, default=str)
    )

    response = social_media_strategy_model.invoke(prompt)

    return {
        "agent_social_media_strategy": response.model_dump(),
        "strategy_feedback": None
    }


# ============================= Social Media Strategy Optimization Agent NODE =============================
@log_calls
def strategy_optimization_node(state: StartupMarketingState):

    logger.info("Optimizing social media strategy")

    optimization_context = {

        "existing_strategy": state.get(
            "agent_social_media_strategy"
        ),

        "founder_feedback": state.get(
            "strategy_feedback"
        ),

        "startup_information": {
            "startup_name": state.get("startup_name"),
            "product_name": state.get("product_name"),
            "product_description": state.get("product_description"),
            "industry": state.get("industry")
        },

        "marketing_goals": state.get("marketing_goals"),

        "startup_analysis": state.get(
            "agent_startup_analysis"
        ),

        "market_research": state.get(
            "agent_market_research"
        ),

        "customer_research": state.get(
            "agent_customer_research"
        )
    }

    prompt = STRATEGY_OPTIMIZATION_PROMPT.format(
        context=json.dumps(optimization_context, indent=2, default=str)
    )

    response = strategy_optimization_model.invoke(prompt)

    logger.info("Strategy successfully optimized")

    return {
        "agent_social_media_strategy": response.model_dump()
    }


# ============================= Human in the Loop Review Loop =============================

from langgraph.types import interrupt, Command


@log_calls
def strategy_review_node(state: StartupMarketingState):

    logger.info("Waiting for founder strategy review")

    review_response = interrupt({
        "message": "Please review the proposed social media strategy.",
        "strategy": state.get("agent_social_media_strategy"),
        "instructions": {
            "approve": "Approve the strategy and proceed to campaign execution.",
            "revise": "Provide feedback to improve the strategy."
        }
    })

    decision = review_response.get("decision", "").strip().lower()

    if decision == "approve":

        logger.info("Strategy approved by founder")

        return Command(
            update={
                "strategy_feedback": None
            },
            goto="campaign_orchestrator"
        )

    elif decision in ["revise", "reject", "feedback"]:

        feedback = review_response.get("feedback", "").strip()

        if not feedback:
            raise ValueError(
                "Founder feedback is required when requesting revisions."
            )

        logger.info("Founder requested strategy revisions")

        return Command(
            update={
                "strategy_feedback": feedback
            },
            goto="strategy_optimization"
        )

    else:
        raise ValueError(
            "Invalid decision. Use 'approve' or 'revise'."
        )




@log_calls
def campaign_orchestrator_node(state: StartupMarketingState):

    logger.info("Starting campaign orchestration")

    campaign_id = start_campaign_orchestration(
        state.get("user_id"),
        state.get("project_id"),
    )

    return {"campaign_id": campaign_id}
