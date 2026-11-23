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
    platform: str
    username: str
    profile_url: str
    account_type: Optional[str] = None


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
