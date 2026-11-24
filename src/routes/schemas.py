from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class SignupRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=255)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=255)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SocialMediaAccountRequest(BaseModel):
    platform: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=1, max_length=255)
    profile_url: str = Field(min_length=1, max_length=500)
    account_type: Optional[str] = None
    connected_account_id: Optional[str] = None
    platform_account_id: Optional[str] = None
    connection_status: Literal["connected", "pending", "disconnected"] = "pending"
    publishing_enabled: bool = False
    publishing_scopes: List[str] = Field(default_factory=list)
    token_expires_at: Optional[str] = None

    @model_validator(mode="after")
    def validate_publishing_details(self):
        if not self.publishing_enabled:
            return self
        missing = []
        if self.connection_status != "connected":
            missing.append("connection_status must be connected")
        if not self.connected_account_id:
            missing.append("connected_account_id")
        if not self.platform_account_id:
            missing.append("platform_account_id")
        if not self.publishing_scopes:
            missing.append("publishing_scopes")
        if missing:
            raise ValueError(
                "Publishing-enabled accounts require: " + ", ".join(missing)
            )
        return self


class StartupDataRequest(BaseModel):
    startup_name: str = Field(min_length=1, max_length=255)
    website_url: str = Field(min_length=1, max_length=500)
    product_name: str = Field(min_length=1, max_length=255)
    product_description: str = Field(min_length=1)
    industry: str = Field(min_length=1, max_length=255)
    marketing_goals: List[str] = Field(min_length=1)

    product_pricing: Optional[str] = None
    main_competitors: Optional[List[str]] = None
    ideal_customers: Optional[str] = None
    target_market: Optional[str] = None
    customer_pain_points: Optional[List[str]] = None
    existing_customer_base: Optional[str] = None
    brand_tone: Optional[str] = None
    brand_identity: Optional[str] = None
    campaign_duration: Optional[str] = None
    social_media_accounts: Optional[List[SocialMediaAccountRequest]] = None
    brand_logo: Optional[str] = None
    brand_assets: Optional[List[str]] = None


class BrandUploadResponse(BaseModel):
    brand_logo: Optional[str] = None
    brand_assets: list[str] = []
    project_id: Optional[int] = None


class RunAcceptedResponse(BaseModel):
    project_id: int
    thread_id: str
    workflow_status: str
    message: str


class RunStatusResponse(BaseModel):
    project_id: int
    thread_id: Optional[str]
    workflow_status: str
    outputs: dict
    current_agents: List[str] = []
    campaign_id: Optional[int] = None


class RunSummaryResponse(BaseModel):
    project_id: int
    startup_name: str
    workflow_status: str
    thread_id: Optional[str]


class ReviewRequest(BaseModel):
    decision: Literal["approve", "revise", "reject", "feedback"]
    feedback: Optional[str] = None

    @model_validator(mode="after")
    def feedback_required_for_revision(self):
        if self.decision != "approve" and not self.feedback:
            raise ValueError("feedback is required when requesting a revision")
        return self


class AssetConfirmationItem(BaseModel):
    assignment_id: int = Field(gt=0)
    action: Literal["accepted", "rejected"]
    asset_id: Optional[int] = Field(default=None, gt=0)
    requirement_id: Optional[int] = Field(default=None, gt=0)
    carousel_position: Optional[int] = Field(default=None, ge=0)


class AssetConfirmationRequest(BaseModel):
    confirmations: List[AssetConfirmationItem] = Field(min_length=1)


class ManualAssetAssignmentRequest(BaseModel):
    post_id: int = Field(gt=0)
    asset_id: int = Field(gt=0)
    requirement_id: Optional[int] = Field(default=None, gt=0)
    carousel_position: Optional[int] = Field(default=None, ge=0)


class PostReviewRequest(BaseModel):
    decision: Literal["approve", "revision"]
    note: Optional[str] = None

    @model_validator(mode="after")
    def note_required_for_revision(self):
        if self.decision == "revision" and not self.note:
            raise ValueError("note is required when requesting a revision")
        return self


class CampaignActionResponse(BaseModel):
    campaign_id: Optional[int] = None
    status: str
    message: str
    count: Optional[int] = None
