from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from src.agents.graph.state import SocialMediaStrategyOutput
from src.utilis.logging import log_calls
from src.agents.graph.campaign_state import (
    AssetMatchOutput,
    CampaignPlanOutput,
    ContentPlanOutput,
)

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

# GEMINI_MODEL = "gemini-3.5-flash-lite"
GEMINI_MODEL = "gemini-3.6-flash"
GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_TEMPERATURE = 0.2


@log_calls
def _gemini_llm(max_retries: int = 0) -> ChatGoogleGenerativeAI:
    if max_retries:
        return ChatGoogleGenerativeAI(model=GEMINI_MODEL, max_retries=max_retries)
    return ChatGoogleGenerativeAI(model=GEMINI_MODEL)


@log_calls
def _groq_llm() -> ChatGroq:
    return ChatGroq(model_name=GROQ_MODEL, temperature=GROQ_TEMPERATURE)


@log_calls
def _gemini_with_groq_fallback(max_retries: int = 0):
    return _gemini_llm(max_retries).with_fallbacks([_groq_llm()])


@log_calls
def _structured_model_with_fallback(schema, max_retries: int = 0):
    primary = _gemini_llm(max_retries).with_structured_output(schema)
    fallback = _groq_llm().with_structured_output(schema)
    return primary.with_fallbacks([fallback])


startup_analysis_llm = _groq_llm()

market_research_llm = _gemini_with_groq_fallback(max_retries=3)
customer_research_llm = _gemini_with_groq_fallback(max_retries=3)

social_media_strategy_llm = _gemini_with_groq_fallback()
strategy_optimization_llm = _gemini_with_groq_fallback()

social_media_strategy_model = _structured_model_with_fallback(
    SocialMediaStrategyOutput
)
strategy_optimization_model = _structured_model_with_fallback(
    SocialMediaStrategyOutput
)

campaign_llm = _gemini_with_groq_fallback()
campaign_plan_model = _structured_model_with_fallback(CampaignPlanOutput)

asset_analysis_llm = _gemini_with_groq_fallback(max_retries=3)
asset_matching_model = _structured_model_with_fallback(
    AssetMatchOutput,
    max_retries=3,
)

content_preparation_llm = _gemini_with_groq_fallback()
content_preparation_model = _structured_model_with_fallback(ContentPlanOutput)
