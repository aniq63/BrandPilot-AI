from datetime import date, datetime
from typing import Annotated, Any, Literal, Optional, TypedDict

from pydantic import BaseModel, Field


class AssetRequirementOutput(BaseModel):
    media_type: Literal["image", "video", "carousel", "other"]
    description: str = Field(min_length=1)
    position: int = Field(default=0, ge=0)
    quantity: int = Field(default=1, ge=1)
    required: bool = True


class CampaignPostOutput(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    objective: str = Field(min_length=1)
    format: str = Field(min_length=1, max_length=100)
    platform: str = Field(min_length=1, max_length=100)
    caption_direction: str = Field(min_length=1)
    scheduled_at: Optional[datetime] = None
    requirements: list[AssetRequirementOutput] = Field(default_factory=list)


class CampaignPlanOutput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    campaign_duration: str = Field(min_length=1, max_length=255)
    objectives: list[str] = Field(min_length=1)
    posts: list[CampaignPostOutput] = Field(min_length=1)


class AssetCandidateInput(BaseModel):
    id: int
    file_name: str
    file_type: str
    mime_type: str
    public_url: str


class PostCandidateInput(BaseModel):
    id: int
    topic: str
    platform: str
    requirements: list[dict[str, Any]] = Field(default_factory=list)


class AssetSuggestionOutput(BaseModel):
    post_id: int
    asset_id: int
    requirement_id: Optional[int] = None
    carousel_position: Optional[int] = Field(default=None, ge=0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str = Field(min_length=1)


class AssetMatchOutput(BaseModel):
    suggestions: list[AssetSuggestionOutput] = Field(default_factory=list)
    unmet_requirements: list[str] = Field(default_factory=list)


class PreparedContentOutput(BaseModel):
    post_id: int
    platform: str = Field(min_length=1, max_length=100)
    caption: str = Field(min_length=1)
    hashtags: list[str] = Field(default_factory=list)
    cta: str = Field(default="")
    content: dict[str, Any] = Field(default_factory=dict)
    validation_notes: str = Field(default="")


class ContentPlanOutput(BaseModel):
    drafts: list[PreparedContentOutput] = Field(min_length=1)


class CampaignOrchestratorState(TypedDict):
    user_id: Annotated[int, "Authenticated founder that owns the project."]
    project_id: Annotated[int, "StartupMarketingData row id."]
    context: Annotated[dict[str, Any], "Approved strategy and startup context."]
    plan: Annotated[Optional[dict[str, Any]], "Structured campaign plan produced by the orchestrator."]


class AssetMatchingState(TypedDict):
    user_id: Annotated[int, "Authenticated founder that owns the campaign."]
    project_id: Annotated[int, "StartupMarketingData row id."]
    campaign_id: Annotated[int, "Campaign row id."]
    posts: Annotated[list[dict[str, Any]], "Posts with their asset requirements."]
    assets: Annotated[list[dict[str, Any]], "Uploaded campaign assets."]
    suggestions: Annotated[Optional[dict[str, Any]], "AI-generated asset suggestions."]


class ContentPreparationState(TypedDict):
    user_id: Annotated[int, "Authenticated founder that owns the campaign."]
    project_id: Annotated[int, "StartupMarketingData row id."]
    campaign_id: Annotated[int, "Campaign row id."]
    posts: Annotated[list[dict[str, Any]], "Posts with confirmed assets."]
    strategy: Annotated[dict[str, Any], "Approved social media strategy."]
    drafts: Annotated[Optional[dict[str, Any]], "Prepared post drafts."]
