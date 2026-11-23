
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    JSON
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
        nullable=False
    )

    social_media_accounts: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=False
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
