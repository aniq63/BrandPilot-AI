
from datetime import date, datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    Text,
    DateTime,
    Date,
    Boolean,
    Float,
    ForeignKey,
    JSON,
    UniqueConstraint,
    text
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)


class Base(DeclarativeBase):
    pass


# ==========================================
# USER TABLE
# ==========================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # One user can have many startup marketing projects
    startups: Mapped[List["StartupMarketingData"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )


# ==========================================
# STARTUP MARKETING DATA TABLE
# ==========================================

class StartupMarketingData(Base):
    __tablename__ = "startup_marketing_data"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    thread_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )

    workflow_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default=text("'pending'")
    )

    current_agents: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True
    )

    # Foreign Key: Each startup belongs to one user
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ==========================================
    # A. Startup Information
    # ==========================================

    startup_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    website_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    product_description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    industry: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    product_pricing: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    main_competitors: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True
    )

    # ==========================================
    # B. Target Audience
    # ==========================================

    ideal_customers: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    target_market: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    customer_pain_points: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True
    )

    existing_customer_base: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # ==========================================
    # C. Marketing Goals
    # ==========================================

    marketing_goals: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False
    )

    # ==========================================
    # D. Marketing Resources
    # ==========================================

    brand_tone: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    brand_identity: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    campaign_duration: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    social_media_accounts: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )

    brand_logo: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True
    )

    # Brand Assets: Multiple image URLs
    brand_assets: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True
    )

    # ==========================================
    # E. Agent Analysis & Research
    # ==========================================

    agent_startup_analysis: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    agent_market_research: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    agent_customer_research: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # ==========================================
    # F. Social Media Strategist Output
    # ==========================================

    agent_social_media_strategy: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )

    # ==========================================
    # G. Strategy Management
    # ==========================================

    strategy_feedback: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # ==========================================
    # Relationships
    # ==========================================

    user: Mapped["User"] = relationship(
        back_populates="startups"
    )

    # ==========================================
    # Timestamps
    # ==========================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    campaigns: Mapped[List["Campaign"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan"
    )

    assets: Mapped[List["CampaignAsset"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan"
    )


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("startup_marketing_data.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        server_default=text("'draft'"),
    )
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    campaign_duration: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    objectives: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    strategy_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    project: Mapped["StartupMarketingData"] = relationship(back_populates="campaigns")
    posts: Mapped[List["CampaignPost"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
    )
    assets: Mapped[List["CampaignAsset"]] = relationship(back_populates="campaign")


class CampaignPost(Base):
    __tablename__ = "campaign_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    objective: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    format: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    caption_direction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="planned",
        server_default=text("'planned'"),
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="posts")
    requirements: Mapped[List["AssetRequirement"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
    )
    prepared_post: Mapped[Optional["PreparedPost"]] = relationship(
        back_populates="post",
        uselist=False,
        cascade="all, delete-orphan",
    )
    assignments: Mapped[List["AssetAssignment"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
    )


class AssetRequirement(Base):
    __tablename__ = "asset_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaign_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    media_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    post: Mapped["CampaignPost"] = relationship(back_populates="requirements")


class CampaignAsset(Base):
    __tablename__ = "campaign_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("startup_marketing_data.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    uploaded_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    storage_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        unique=True,
        index=True,
    )
    public_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="available",
        server_default=text("'available'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    project: Mapped["StartupMarketingData"] = relationship(back_populates="assets")
    campaign: Mapped[Optional["Campaign"]] = relationship(back_populates="assets")
    assignments: Mapped[List["AssetAssignment"]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
    )


class AssetAssignment(Base):
    __tablename__ = "asset_assignments"
    __table_args__ = (
        UniqueConstraint("post_id", "asset_id", name="uq_post_asset"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaign_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaign_assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requirement_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("asset_requirements.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    carousel_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ai",
        server_default=text("'ai'"),
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="suggested",
        server_default=text("'suggested'"),
    )
    confirmed_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    post: Mapped["CampaignPost"] = relationship(back_populates="assignments")
    asset: Mapped["CampaignAsset"] = relationship(back_populates="assignments")


class PreparedPost(Base):
    __tablename__ = "prepared_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaign_posts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    cta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    validation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        server_default=text("'draft'"),
    )
    approved_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    post: Mapped["CampaignPost"] = relationship(back_populates="prepared_post")
    publishing_jobs: Mapped[List["PublishingJob"]] = relationship(
        back_populates="prepared_post",
        cascade="all, delete-orphan",
    )


class PublishingJob(Base):
    __tablename__ = "publishing_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prepared_post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("prepared_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("startup_marketing_data.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    connected_account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    platform_account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    connection_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    publishing_scopes: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="scheduled",
        server_default=text("'scheduled'"),
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    prepared_post: Mapped["PreparedPost"] = relationship(back_populates="publishing_jobs")
