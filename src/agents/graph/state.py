from typing import Annotated, List, Literal, Optional, TypedDict
from pydantic import BaseModel



# ==========================================
# Social Media Startegy STATE
# ==========================================

class SocialMediaStrategyOutput(BaseModel):

    # Overall Strategy
    campaign_objective: str
    overall_strategy: str
    campaign_duration: str

    # Platform Strategy
    selected_platforms: List[str]
    platform_strategies: List[dict]

    # Content Strategy
    content_pillars: List[str]
    content_themes: List[str]
    brand_voice: str
    content_frequency: str

    # Campaign Planning
    campaign_ideas: List[dict]
    hashtag_strategy: List[str]
    call_to_action: List[str]

    # Audience Targeting
    audience_segments: List[dict]
    messaging_strategy: str

    # Performance Metrics
    success_metrics: List[str]
    expected_outcomes: List[str]

    # Recommendations
    recommendations: List[str]


# ==========================================
# Social Media Account STATE
# ==========================================
class SocialMediaAccount(TypedDict):

    platform: str
    username: str
    profile_url: str
    account_type: Optional[str]
    connected_account_id: Optional[str]
    platform_account_id: Optional[str]
    connection_status: Optional[str]
    publishing_enabled: Optional[bool]
    publishing_scopes: Optional[List[str]]
    token_expires_at: Optional[str]

    # Managed by the integration system
    analytics_enabled: Optional[bool]


# ==========================================
# MAIN STARTUP MARKETING STATE
# ==========================================

class StartupMarketingState(TypedDict):

    user_id: Annotated[Optional[int], "Authenticated user that owns this run."]
    project_id: Annotated[Optional[int], "StartupMarketingData row id for this run."]
    thread_id: Annotated[Optional[str], "Unique LangGraph thread id for this run."]

    # A. Startup Information
    startup_name: Annotated[str, "The official name of the startup."]
    website_url: Annotated[str, "The official website URL of the startup."]
    product_name: Annotated[str, "The name of the startup's primary product or service."]
    product_description: Annotated[str, "A description of the product, its features, purpose, and the problem it solves."]
    industry: Annotated[str, "The industry or market sector in which the startup operates."]
    product_pricing: Annotated[Optional[str], "The product's pricing model, subscription fees, free plans, or custom pricing."]
    main_competitors: Annotated[Optional[List[str]], "The startup's main direct and indirect competitors."]

    # B. Target Audience
    ideal_customers: Annotated[Optional[str], "A description of the startup's ideal customers and customer segments."]
    target_market: Annotated[Optional[str], "The geographical locations, countries, or regions targeted by the startup."]
    customer_pain_points: Annotated[Optional[List[str]], "The problems and challenges faced by target customers that the product solves."]
    existing_customer_base: Annotated[Optional[str], "Information about the startup's existing customers and user base, if available."]

    # C. Marketing Goals
    marketing_goals: Annotated[List[str], "The startup's marketing objectives, such as brand awareness, lead generation, customer acquisition, increasing conversions, or product launches."]

    # D. Marketing Resources
    brand_tone: Annotated[Optional[str], "The preferred communication style and personality of the brand."]
    brand_identity: Annotated[Optional[str], "The brand's visual identity, positioning, values, colors, and typography."]
    campaign_duration: Annotated[Optional[str], "The preferred duration of the marketing campaign."]

    social_media_accounts: Annotated[
        Optional[List[SocialMediaAccount]],
        "Social media accounts supplied by the startup, including profile details, publishing connection identifiers, permission scopes, token expiry, and system-managed analytics status."
    ]

    brand_logo: Annotated[Optional[str], "The logo image URL or reference to the uploaded brand logo."]
    brand_assets: Annotated[Optional[List[str]], "References or URLs for additional brand assets, such as product images, banners, and brand guidelines."]

    # E. Agent Analysis & Research
    agent_startup_analysis: Annotated[Optional[str], "Comprehensive analysis of the startup, its product, value proposition, business model, positioning, strengths, and weaknesses."]

    agent_market_research: Annotated[Optional[str], "Market research covering industry trends, market size, opportunities, threats, market demand, and competitor analysis."]

    agent_customer_research: Annotated[Optional[str], "Customer research covering ideal customer personas, demographics, behavior, needs, pain points, motivations, and purchasing decisions."]

    # F. Social Media Strategist Output
    agent_social_media_strategy: Annotated[Optional[dict], "Structured social media marketing strategy generated using startup analysis, market research, and customer research."]

    # G. Strategy Management
    strategy_feedback: Annotated[
        Optional[str],
        "Founder feedback, requested changes, or revision instructions for the proposed social media strategy."
    ]

    campaign_id: Annotated[
        Optional[int],
        "Campaign created after the founder approves the social media strategy."
    ]
