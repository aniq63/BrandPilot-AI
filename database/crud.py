from typing import Any, Optional

from sqlalchemy.orm import Session

from database.models import StartupMarketingData, User

STARTUP_INPUT_FIELDS = (
    "startup_name",
    "website_url",
    "product_name",
    "product_description",
    "industry",
    "product_pricing",
    "main_competitors",
    "ideal_customers",
    "target_market",
    "customer_pain_points",
    "existing_customer_base",
    "marketing_goals",
    "brand_tone",
    "brand_identity",
    "campaign_duration",
    "social_media_accounts",
    "brand_logo",
    "brand_assets",
)

OUTPUT_COLUMNS = (
    "agent_startup_analysis",
    "agent_market_research",
    "agent_customer_research",
    "agent_social_media_strategy",
    "strategy_feedback",
)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.lower()).first()


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    username: str,
    email: str,
    password_hash: str,
) -> User:
    user = User(
        username=username,
        email=email.lower(),
        password=password_hash,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_startup_data(
    db: Session,
    user_id: int,
    payload: dict[str, Any],
    thread_id: str,
) -> StartupMarketingData:
    values = {field: payload.get(field) for field in STARTUP_INPUT_FIELDS}
    project = StartupMarketingData(
        user_id=user_id,
        thread_id=thread_id,
        workflow_status="running",
        **values,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_startup_data(
    db: Session,
    project_id: int,
    user_id: int,
) -> Optional[StartupMarketingData]:
    return (
        db.query(StartupMarketingData)
        .filter(
            StartupMarketingData.id == project_id,
            StartupMarketingData.user_id == user_id,
        )
        .first()
    )


def list_user_projects(
    db: Session,
    user_id: int,
) -> list[StartupMarketingData]:
    return (
        db.query(StartupMarketingData)
        .filter(StartupMarketingData.user_id == user_id)
        .order_by(StartupMarketingData.id.desc())
        .all()
    )


def update_agent_outputs(
    db: Session,
    project_id: int,
    outputs: dict[str, Any],
) -> None:
    project = db.query(StartupMarketingData).filter(
        StartupMarketingData.id == project_id
    ).first()
    if project is None:
        return

    for column in OUTPUT_COLUMNS:
        if column in outputs:
            setattr(project, column, outputs[column])

    db.commit()


def update_brand_media(
    db: Session,
    project_id: int,
    brand_logo: Optional[str] = None,
    brand_assets: Optional[list[str]] = None,
) -> None:
    project = db.query(StartupMarketingData).filter(
        StartupMarketingData.id == project_id
    ).first()
    if project is None:
        return

    if brand_logo is not None:
        project.brand_logo = brand_logo

    if brand_assets:
        existing = project.brand_assets or []
        project.brand_assets = existing + [
            url for url in brand_assets if url not in existing
        ]

    db.commit()


def update_workflow_status(
    db: Session,
    project_id: int,
    status: str,
) -> None:
    db.query(StartupMarketingData).filter(
        StartupMarketingData.id == project_id
    ).update({"workflow_status": status})
    db.commit()
