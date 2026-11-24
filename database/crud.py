import json
from typing import Any, Optional

from pydantic import BaseModel
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

JSON_OUTPUT_COLUMNS = frozenset({"agent_social_media_strategy"})


def _serialize_text_output(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                parts.append(text if isinstance(text, str) else json.dumps(item, ensure_ascii=False))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    if isinstance(value, dict):
        text = value.get("text")
        return text if isinstance(text, str) else json.dumps(value, ensure_ascii=False)
    return str(value)


def _serialize_json_output(value: Any) -> Any:
    if value is None or isinstance(value, (dict, list)):
        return value
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return {"raw": value}
    return value


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
            value = outputs[column]
            if column in JSON_OUTPUT_COLUMNS:
                value = _serialize_json_output(value)
            else:
                value = _serialize_text_output(value)
            setattr(project, column, value)

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


def update_current_agents(
    db: Session,
    project_id: int,
    current_agents: list[str] | None,
) -> None:
    db.query(StartupMarketingData).filter(
        StartupMarketingData.id == project_id
    ).update({"current_agents": current_agents})
    db.commit()
