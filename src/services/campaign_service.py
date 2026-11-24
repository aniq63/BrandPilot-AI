from datetime import date, datetime, timezone
from typing import Any, Optional

from database.connection import SessionLocal
from database.models import (
    Campaign,
    CampaignAsset,
    CampaignPost,
    PreparedPost,
    PublishingJob,
)
from database.repositories import CampaignRepository
from src.agents.graph.asset_matching import asset_matching_app
from src.agents.graph.campaign_orchestrator import campaign_orchestrator_app
from src.agents.graph.content_preparation import content_preparation_app
from src.utilis.logging import log_calls


def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _as_datetime(value: Any) -> Optional[datetime]:
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _as_date(value: Any) -> Optional[date]:
    if value is None or isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


@log_calls
def build_project_context(project: Any) -> dict[str, Any]:
    return {
        "startup_information": {
            "startup_name": project.startup_name,
            "website_url": project.website_url,
            "product_name": project.product_name,
            "product_description": project.product_description,
            "industry": project.industry,
            "product_pricing": project.product_pricing,
            "brand_tone": project.brand_tone,
            "brand_identity": project.brand_identity,
        },
        "marketing_goals": project.marketing_goals or [],
        "approved_strategy": project.agent_social_media_strategy or {},
        "startup_analysis": project.agent_startup_analysis,
        "market_research": project.agent_market_research,
        "customer_research": project.agent_customer_research,
        "campaign_duration": project.campaign_duration,
        "social_media_accounts": project.social_media_accounts or [],
        "brand_logo": project.brand_logo,
        "brand_assets": project.brand_assets or [],
    }


def _connected_account_map(project: Any) -> dict[str, dict[str, Any]]:
    raw = project.social_media_accounts or {}
    entries: list[dict[str, Any]] = []
    if isinstance(raw, dict):
        if isinstance(raw.get("platforms"), list):
            entries = [item for item in raw["platforms"] if isinstance(item, dict)]
        elif isinstance(raw.get("accounts"), list):
            entries = [item for item in raw["accounts"] if isinstance(item, dict)]
    elif isinstance(raw, list):
        entries = [item for item in raw if isinstance(item, dict)]

    result: dict[str, dict[str, Any]] = {}
    for entry in entries:
        platform = entry.get("platform")
        account_id = entry.get("connected_account_id")
        page_id = entry.get("platform_account_id")
        scopes = entry.get("publishing_scopes") or []
        connected = str(entry.get("connection_status") or "").lower() == "connected"
        publishing_enabled = entry.get("publishing_enabled") is True
        if platform and account_id and page_id and scopes and connected and publishing_enabled:
            result[str(platform).lower()] = {
                "connected_account_id": str(account_id),
                "platform_account_id": str(page_id),
                "connection_status": "connected",
                "publishing_scopes": list(scopes),
                "token_expires_at": entry.get("token_expires_at"),
            }
    return result


def _import_brand_assets(
    repo: CampaignRepository,
    project: Any,
    campaign_id: int,
    user_id: int,
) -> None:
    existing_paths = {
        asset.storage_path for asset in repo.list_assets(project.id, campaign_id)
    }
    candidates: list[tuple[str, Optional[str]]] = []
    if project.brand_logo:
        candidates.append((project.brand_logo, "logo"))
    for url in project.brand_assets or []:
        candidates.append((url, None))

    payloads: list[dict[str, Any]] = []
    for url, _ in candidates:
        if not isinstance(url, str) or url in existing_paths:
            continue
        existing_paths.add(url)
        payloads.append(
            {
                "storage_path": url,
                "public_url": url,
                "file_name": url.rsplit("/", 1)[-1] or "brand-asset",
                "mime_type": "image/*",
                "file_type": "image",
                "size_bytes": 0,
            }
        )
    if payloads:
        repo.create_assets(project.id, campaign_id, user_id, payloads)


@log_calls
def start_campaign_orchestration(user_id: int, project_id: int) -> Optional[int]:
    with SessionLocal() as db:
        repo = CampaignRepository(db)
        project = repo.get_owned_project(project_id, user_id)
        if project is None:
            return None

        existing = (
            db.query(Campaign)
            .filter(Campaign.project_id == project_id)
            .order_by(Campaign.id.desc())
            .first()
        )
        if existing is not None:
            return existing.id

        context = build_project_context(project)
        result = campaign_orchestrator_app.invoke(
            {
                "user_id": user_id,
                "project_id": project_id,
                "context": context,
                "plan": None,
            }
        )
        plan = result.get("plan") or {}
        strategy = project.agent_social_media_strategy or {}
        approved_platforms = {
            str(item).lower()
            for item in strategy.get("selected_platforms", [])
            if isinstance(item, str)
        }

        posts: list[dict[str, Any]] = []
        for raw_post in plan.get("posts", []):
            platform = str(raw_post.get("platform", ""))
            if approved_platforms and platform.lower() not in approved_platforms:
                continue
            posts.append(
                {
                    "position": len(posts),
                    "topic": raw_post["topic"],
                    "objective": raw_post.get("objective"),
                    "format": raw_post.get("format"),
                    "platform": platform,
                    "caption_direction": raw_post.get("caption_direction"),
                    "scheduled_at": _as_datetime(raw_post.get("scheduled_at")),
                    "requirements": [
                        dict(requirement)
                        for requirement in raw_post.get("requirements", [])
                    ],
                }
            )
        if not posts:
            raise ValueError(
                "Campaign plan did not contain posts on approved platforms."
            )

        campaign = repo.create_campaign(
            project_id=project_id,
            name=plan.get("name") or f"{project.startup_name} Campaign",
            strategy_snapshot=strategy,
        )
        db.query(Campaign).filter(Campaign.id == campaign.id).update(
            {
                "start_date": _as_date(plan.get("start_date")),
                "end_date": _as_date(plan.get("end_date")),
                "campaign_duration": plan.get("campaign_duration"),
                "objectives": plan.get("objectives", []),
            }
        )
        repo.replace_campaign_posts(campaign.id, posts)
        _import_brand_assets(repo, project, campaign.id, user_id)
        repo.set_campaign_status(campaign.id, "assets_pending")
        return campaign.id


@log_calls
def run_asset_matching(user_id: int, campaign_id: int) -> int:
    with SessionLocal() as db:
        repo = CampaignRepository(db)
        campaign = repo.get_campaign(campaign_id, user_id)
        if campaign is None:
            raise LookupError("Campaign not found.")

        post_rows = repo.get_posts(campaign_id)
        posts = [
            {
                "id": post.id,
                "topic": post.topic,
                "platform": post.platform,
                "requirements": [
                    {
                        "id": requirement.id,
                        "media_type": requirement.media_type,
                        "description": requirement.description,
                        "position": requirement.position,
                        "quantity": requirement.quantity,
                        "required": requirement.required,
                    }
                    for requirement in post.requirements
                ],
            }
            for post in post_rows
        ]
        assets = [
            asset_to_dict(asset) for asset in repo.list_assets(campaign.project_id)
        ]
        if not assets:
            raise ValueError("Upload campaign assets before requesting suggestions.")

        result = asset_matching_app.invoke(
            {
                "user_id": user_id,
                "project_id": campaign.project_id,
                "campaign_id": campaign_id,
                "posts": posts,
                "assets": assets,
                "suggestions": None,
            }
        )

        post_by_id = {post.id: post for post in post_rows}
        asset_by_id = {asset["id"]: asset for asset in assets}
        requirement_by_post = {
            post.id: {requirement.id for requirement in post.requirements}
            for post in post_rows
        }

        suggestions: list[dict[str, Any]] = []
        for raw in (result.get("suggestions") or {}).get("suggestions", []):
            post_id = raw.get("post_id")
            asset_id = raw.get("asset_id")
            requirement_id = raw.get("requirement_id")
            if post_id not in post_by_id or asset_id not in asset_by_id:
                continue
            if requirement_id is not None:
                if requirement_id not in requirement_by_post[post_id]:
                    continue
            suggestions.append(
                {
                    "post_id": post_id,
                    "asset_id": asset_id,
                    "requirement_id": requirement_id,
                    "carousel_position": raw.get("carousel_position"),
                    "confidence": raw.get("confidence", 0.0),
                    "explanation": raw.get("explanation", ""),
                }
            )

        repo.replace_suggestions(campaign_id, suggestions)
        repo.set_campaign_status(campaign_id, "asset_analysis_ready")
        return len(suggestions)


@log_calls
def confirm_asset_assignments(
    user_id: int,
    campaign_id: int,
    decisions: list[dict[str, Any]],
) -> int:
    with SessionLocal() as db:
        repo = CampaignRepository(db)
        campaign = repo.get_campaign(campaign_id, user_id)
        if campaign is None:
            raise LookupError("Campaign not found.")

        count = 0
        for decision in decisions:
            assignment = repo.get_assignment(decision["assignment_id"], campaign_id)
            if assignment is None:
                raise LookupError(
                    f"Assignment {decision['assignment_id']} not found in campaign."
                )
            updates: dict[str, Any] = {}
            asset_id = decision.get("asset_id")
            if asset_id is not None:
                asset = repo.get_asset(asset_id, user_id)
                if asset is None or asset.project_id != campaign.project_id:
                    raise LookupError(f"Asset {asset_id} not found in project.")
                updates["asset_id"] = asset_id
            if "requirement_id" in decision:
                updates["requirement_id"] = decision["requirement_id"]
            if "carousel_position" in decision:
                updates["carousel_position"] = decision["carousel_position"]
            repo.confirm_assignment(
                assignment,
                user_id,
                decision["action"],
                updates,
            )
            count += 1
        repo.set_campaign_status(campaign_id, "assets_confirmed")
        return count


@log_calls
def add_manual_asset_assignment(
    user_id: int,
    campaign_id: int,
    post_id: int,
    asset_id: int,
    requirement_id: Optional[int] = None,
    carousel_position: Optional[int] = None,
) -> dict[str, Any]:
    with SessionLocal() as db:
        repo = CampaignRepository(db)
        campaign = repo.get_campaign(campaign_id, user_id)
        post = repo.get_post(post_id, user_id)
        asset = repo.get_asset(asset_id, user_id)
        if campaign is None or post is None or post.campaign_id != campaign_id:
            raise LookupError("Post not found in campaign.")
        if asset is None or asset.project_id != campaign.project_id:
            raise LookupError("Asset not found in project.")
        if requirement_id is not None and requirement_id not in {
            requirement.id for requirement in post.requirements
        }:
            raise LookupError("Requirement not found in post.")
        assignment = repo.add_manual_assignment(
            post_id,
            asset_id,
            requirement_id,
            user_id,
            carousel_position,
        )
        return assignment_to_dict(assignment)


@log_calls
def regenerate_asset_suggestions(user_id: int, campaign_id: int) -> int:
    with SessionLocal() as db:
        repo = CampaignRepository(db)
        campaign = repo.get_campaign(campaign_id, user_id)
        if campaign is None:
            raise LookupError("Campaign not found.")
        repo.clear_assignments(campaign_id)
        repo.set_campaign_status(campaign_id, "assets_pending")
    return run_asset_matching(user_id, campaign_id)


@log_calls
def run_content_preparation(user_id: int, campaign_id: int) -> int:
    with SessionLocal() as db:
        repo = CampaignRepository(db)
        campaign = repo.get_campaign(campaign_id, user_id)
        if campaign is None:
            raise LookupError("Campaign not found.")
        project = repo.get_owned_project(campaign.project_id, user_id)
        if project is None:
            raise LookupError("Project not found.")

        post_rows = repo.get_posts(campaign_id)
        posts_data: list[dict[str, Any]] = []
        for post in post_rows:
            confirmed_assets = [
                {
                    "asset_id": assignment.asset_id,
                    "file_name": assignment.asset.file_name,
                    "public_url": assignment.asset.public_url,
                    "carousel_position": assignment.carousel_position,
                    "explanation": assignment.explanation,
                }
                for assignment in post.assignments
                if assignment.status == "accepted"
            ]
            posts_data.append(
                {
                    "id": post.id,
                    "topic": post.topic,
                    "objective": post.objective,
                    "format": post.format,
                    "platform": post.platform,
                    "caption_direction": post.caption_direction,
                    "scheduled_at": _iso(post.scheduled_at),
                    "confirmed_assets": confirmed_assets,
                }
            )
        if not posts_data:
            raise ValueError("Campaign has no posts to prepare.")

        result = content_preparation_app.invoke(
            {
                "user_id": user_id,
                "project_id": campaign.project_id,
                "campaign_id": campaign_id,
                "posts": posts_data,
                "strategy": project.agent_social_media_strategy or {},
                "drafts": None,
            }
        )

        valid_post_ids = {post.id for post in post_rows}
        platform_by_id = {post.id: post.platform for post in post_rows}
        drafts = []
        for raw in (result.get("drafts") or {}).get("drafts", []):
            if raw.get("post_id") not in valid_post_ids:
                continue
            drafts.append(
                {
                    "post_id": raw["post_id"],
                    "platform": raw.get("platform")
                    or platform_by_id[raw["post_id"]],
                    "caption": raw["caption"],
                    "hashtags": raw.get("hashtags", []),
                    "cta": raw.get("cta", ""),
                    "content": raw.get("content", {}),
                    "validation_notes": raw.get("validation_notes", ""),
                }
            )
        repo.upsert_prepared_posts(campaign_id, drafts)
        repo.set_campaign_status(campaign_id, "content_ready")
        return len(drafts)


@log_calls
def regenerate_content(user_id: int, campaign_id: int) -> int:
    with SessionLocal() as db:
        repo = CampaignRepository(db)
        campaign = repo.get_campaign(campaign_id, user_id)
        if campaign is None:
            raise LookupError("Campaign not found.")

        db.query(PublishingJob).filter(
            PublishingJob.project_id == campaign.project_id
        ).delete(synchronize_session=False)
        post_ids = [post.id for post in repo.get_posts(campaign_id)]
        if post_ids:
            db.query(PreparedPost).filter(
                PreparedPost.post_id.in_(post_ids)
            ).delete(synchronize_session=False)
            db.query(CampaignPost).filter(
                CampaignPost.id.in_(post_ids)
            ).update({"status": "planned"}, synchronize_session=False)
        repo.set_campaign_status(campaign_id, "assets_confirmed")

    return run_content_preparation(user_id, campaign_id)


@log_calls
def review_prepared_post(
    user_id: int,
    prepared_post_id: int,
    decision: str,
    note: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    with SessionLocal() as db:
        repo = CampaignRepository(db)
        prepared = repo.get_prepared_post(prepared_post_id, user_id)
        if prepared is None:
            return None
        if decision == "approve":
            repo.approve_prepared_post(prepared, user_id)
        else:
            repo.request_revision(prepared, note or "")
        return prepared_to_dict(prepared)


@log_calls
def create_publishing_jobs(
    user_id: int,
    campaign_id: int,
) -> list[dict[str, Any]]:
    with SessionLocal() as db:
        repo = CampaignRepository(db)
        campaign = repo.get_campaign(campaign_id, user_id)
        if campaign is None:
            raise LookupError("Campaign not found.")
        project = repo.get_owned_project(campaign.project_id, user_id)
        if project is None:
            raise LookupError("Project not found.")

        prepared_posts = [
            post.prepared_post
            for post in repo.get_posts(campaign_id)
            if post.prepared_post is not None
        ]
        jobs = repo.create_publishing_jobs(
            prepared_posts,
            _connected_account_map(project),
        )
        if jobs:
            repo.set_campaign_status(campaign_id, "publishing_scheduled")
        return [job_to_dict(job) for job in jobs]


def asset_to_dict(asset: CampaignAsset) -> dict[str, Any]:
    return {
        "id": asset.id,
        "project_id": asset.project_id,
        "campaign_id": asset.campaign_id,
        "file_name": asset.file_name,
        "public_url": asset.public_url,
        "storage_path": asset.storage_path,
        "mime_type": asset.mime_type,
        "file_type": asset.file_type,
        "size_bytes": asset.size_bytes,
        "status": asset.status,
    }


def assignment_to_dict(assignment: Any) -> dict[str, Any]:
    return {
        "id": assignment.id,
        "post_id": assignment.post_id,
        "asset_id": assignment.asset_id,
        "requirement_id": assignment.requirement_id,
        "carousel_position": assignment.carousel_position,
        "confidence": assignment.confidence,
        "explanation": assignment.explanation,
        "source": assignment.source,
        "status": assignment.status,
    }


def prepared_to_dict(prepared: Any) -> dict[str, Any]:
    return {
        "id": prepared.id,
        "post_id": prepared.post_id,
        "platform": prepared.platform,
        "caption": prepared.caption,
        "hashtags": prepared.hashtags or [],
        "cta": prepared.cta,
        "content": prepared.content or {},
        "validation_notes": prepared.validation_notes,
        "status": prepared.status,
        "approved_at": _iso(prepared.approved_at),
    }


def job_to_dict(job: Any) -> dict[str, Any]:
    return {
        "id": job.id,
        "prepared_post_id": job.prepared_post_id,
        "project_id": job.project_id,
        "platform": job.platform,
        "connected_account_id": job.connected_account_id,
        "platform_account_id": job.platform_account_id,
        "connection_status": job.connection_status,
        "publishing_scopes": job.publishing_scopes or [],
        "token_expires_at": _iso(job.token_expires_at),
        "scheduled_at": _iso(job.scheduled_at),
        "status": job.status,
        "attempts": job.attempts,
    }


def post_to_dict(post: CampaignPost) -> dict[str, Any]:
    return {
        "id": post.id,
        "position": post.position,
        "topic": post.topic,
        "objective": post.objective,
        "format": post.format,
        "platform": post.platform,
        "caption_direction": post.caption_direction,
        "scheduled_at": _iso(post.scheduled_at),
        "status": post.status,
        "requirements": [
            {
                "id": requirement.id,
                "media_type": requirement.media_type,
                "description": requirement.description,
                "position": requirement.position,
                "quantity": requirement.quantity,
                "required": requirement.required,
            }
            for requirement in post.requirements
        ],
        "assignments": [
            assignment_to_dict(assignment) for assignment in post.assignments
        ],
        "prepared_post": prepared_to_dict(post.prepared_post)
        if post.prepared_post
        else None,
    }


def campaign_to_dict(campaign: Campaign) -> dict[str, Any]:
    return {
        "id": campaign.id,
        "project_id": campaign.project_id,
        "name": campaign.name,
        "status": campaign.status,
        "start_date": _iso(campaign.start_date),
        "end_date": _iso(campaign.end_date),
        "campaign_duration": campaign.campaign_duration,
        "objectives": campaign.objectives or [],
        "posts": [post_to_dict(post) for post in campaign.posts],
        "assets": [asset_to_dict(asset) for asset in campaign.assets],
    }


@log_calls
def get_campaign_details(
    user_id: int,
    campaign_id: int,
) -> Optional[dict[str, Any]]:
    with SessionLocal() as db:
        repo = CampaignRepository(db)
        campaign = repo.get_campaign(campaign_id, user_id)
        if campaign is None:
            return None
        return campaign_to_dict(campaign)


@log_calls
def get_publishing_jobs(
    user_id: int,
    campaign_id: int,
) -> Optional[list[dict[str, Any]]]:
    with SessionLocal() as db:
        repo = CampaignRepository(db)
        campaign = repo.get_campaign(campaign_id, user_id)
        if campaign is None:
            return None
        return [job_to_dict(job) for job in repo.list_publishing_jobs(campaign_id)]
