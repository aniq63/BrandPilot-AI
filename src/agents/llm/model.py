from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from src.agents.graph.state import SocialMediaStrategyOutput

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

# ----------- LLM Intialization --------------

# Startup Analyisy LLM
startup_analysis_llm = ChatGroq(
    model_name="openai/gpt-oss-20b",
    temperature=0.2,
)

# Market Research LLM
market_research_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    max_retries=3
)

# Customer Reserach LLm
customer_research_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    max_retries=3
)


# Social Media Strategy & Optimziation LLm

social_media_strategy_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite"
)


strategy_optimization_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite"
)


# Enforce structured output
social_media_strategy_model = (
    social_media_strategy_llm.with_structured_output(
        SocialMediaStrategyOutput
    )
)

strategy_optimization_model = (
    strategy_optimization_llm.with_structured_output(
        SocialMediaStrategyOutput
    )
)


# Campaign LLM
campaign_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite"
)
