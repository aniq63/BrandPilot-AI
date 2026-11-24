import hashlib

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from database.models import User
from database.repositories import CampaignRepository
from src.routes.deps import get_current_user, get_db
from src.routes.schemas import (
    AssetConfirmationRequest,
    CampaignActionResponse,
    ManualAssetAssignmentRequest,
    PostReviewRequest,
)
from src.services import campaign_service
from src.services.supabase_storage import upload_image
from src.utilis.logging import log_calls

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _repo(db: Session) -> CampaignRepository:
    return CampaignRepository(db)


@log_calls
def _owned_campaign(
    db: Session,
    campaign_id: int,
    user_id: int,
):
    campaign = _repo(db).get_campaign(campaign_id, user_id)
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return campaign


@router.post(
    "/from-strategy/{project_id}",
    response_model=CampaignActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@log_calls
def generate_campaign_from_strategy(
    project_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _repo(db).get_owned_project(project_id, current_user.id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    if not project.agent_social_media_strategy:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Approve a social media strategy before generating a campaign",
        )

    background_tasks.add_task(
        campaign_service.start_campaign_orchestration,
        current_user.id,
        project_id,
    )
    return CampaignActionResponse(
        status="running",
        message="Campaign orchestration started. Poll GET /campaigns/{campaign_id}.",
    )


@router.get("/{campaign_id}")
@log_calls
def get_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
):
    campaign = campaign_service.get_campaign_details(current_user.id, campaign_id)
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return campaign


@router.post("/{campaign_id}/assets")
@log_calls
def upload_campaign_assets(
    campaign_id: int,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    campaign = _owned_campaign(db, campaign_id, current_user.id)
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload at least one image",
        )

    payloads: list[dict] = []
    for upload in files:
        content = upload.file.read()
        storage_path, public_url = upload_image(
            user_id=current_user.id,
            project_id=campaign.project_id,
            filename=upload.filename or "asset.jpg",
            content=content,
            content_type=upload.content_type or "image/jpeg",
            folder=f"campaign_{campaign_id}",
        )
        payloads.append(
            {
                "storage_path": storage_path,
                "public_url": public_url,
                "file_name": upload.filename or "asset.jpg",
                "mime_type": upload.content_type or "image/jpeg",
                "file_type": "image",
                "size_bytes": len(content),
                "checksum": hashlib.sha256(content).hexdigest(),
            }
        )

    assets = _repo(db).create_assets(
        campaign.project_id,
        campaign_id,
        current_user.id,
        payloads,
    )
    return {
        "campaign_id": campaign_id,
        "count": len(assets),
        "assets": [campaign_service.asset_to_dict(asset) for asset in assets],
    }


@router.post(
    "/{campaign_id}/asset-suggestions",
    response_model=CampaignActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@log_calls
def request_asset_suggestions(
    campaign_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    campaign = _owned_campaign(db, campaign_id, current_user.id)
    background_tasks.add_task(
        campaign_service.run_asset_matching,
        current_user.id,
        campaign_id,
    )
    return CampaignActionResponse(
        campaign_id=campaign.id,
        status="running",
        message="Asset analysis started. Poll GET /campaigns/{campaign_id}/asset-suggestions.",
    )


@router.get("/{campaign_id}/asset-suggestions")
@log_calls
def list_asset_suggestions(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    campaign = _owned_campaign(db, campaign_id, current_user.id)
    suggestions = [
        assignment
        for post in campaign.posts
        for assignment in post.assignments
    ]
    return {
        "campaign_id": campaign.id,
        "status": campaign.status,
        "suggestions": [
            campaign_service.assignment_to_dict(assignment)
            for assignment in suggestions
        ],
    }


@router.post(
    "/{campaign_id}/asset-suggestions/regenerate",
    response_model=CampaignActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@log_calls
def regenerate_asset_suggestions(
    campaign_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    campaign = _owned_campaign(db, campaign_id, current_user.id)
    background_tasks.add_task(
        campaign_service.regenerate_asset_suggestions,
        current_user.id,
        campaign_id,
    )
    return CampaignActionResponse(
        campaign_id=campaign.id,
        status="running",
        message="Asset suggestions will be regenerated.",
    )


@router.post("/{campaign_id}/asset-assignments/confirm")
@log_calls
def confirm_asset_assignments(
    campaign_id: int,
    payload: AssetConfirmationRequest,
    current_user: User = Depends(get_current_user),
):
    count = campaign_service.confirm_asset_assignments(
        current_user.id,
        campaign_id,
        [item.model_dump(exclude_none=True) for item in payload.confirmations],
    )
    return {"campaign_id": campaign_id, "confirmed": count}


@router.post("/{campaign_id}/asset-assignments")
@log_calls
def add_manual_asset_assignment(
    campaign_id: int,
    payload: ManualAssetAssignmentRequest,
    current_user: User = Depends(get_current_user),
):
    assignment = campaign_service.add_manual_asset_assignment(
        current_user.id,
        campaign_id,
        payload.post_id,
        payload.asset_id,
        payload.requirement_id,
        payload.carousel_position,
    )
    return assignment


@router.post(
    "/{campaign_id}/prepare-content",
    response_model=CampaignActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@log_calls
def prepare_content(
    campaign_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    campaign = _owned_campaign(db, campaign_id, current_user.id)
    background_tasks.add_task(
        campaign_service.run_content_preparation,
        current_user.id,
        campaign_id,
    )
    return CampaignActionResponse(
        campaign_id=campaign.id,
        status="running",
        message="Content preparation started. Poll GET /campaigns/{campaign_id}/posts.",
    )


@router.post(
    "/{campaign_id}/prepare-content/regenerate",
    response_model=CampaignActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@log_calls
def regenerate_content(
    campaign_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    campaign = _owned_campaign(db, campaign_id, current_user.id)
    background_tasks.add_task(
        campaign_service.regenerate_content,
        current_user.id,
        campaign_id,
    )
    return CampaignActionResponse(
        campaign_id=campaign.id,
        status="running",
        message="Content drafts will be regenerated.",
    )


@router.get("/{campaign_id}/posts")
@log_calls
def list_campaign_posts(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    campaign = _owned_campaign(db, campaign_id, current_user.id)
    return {
        "campaign_id": campaign.id,
        "status": campaign.status,
        "posts": [campaign_service.post_to_dict(post) for post in campaign.posts],
    }


@router.post("/posts/{prepared_post_id}/review")
@log_calls
def review_prepared_post(
    prepared_post_id: int,
    payload: PostReviewRequest,
    current_user: User = Depends(get_current_user),
):
    prepared = campaign_service.review_prepared_post(
        current_user.id,
        prepared_post_id,
        payload.decision,
        payload.note,
    )
    if prepared is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prepared post not found",
        )
    return prepared


@router.post("/{campaign_id}/publishing-jobs")
@log_calls
def create_publishing_jobs(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
):
    jobs = campaign_service.create_publishing_jobs(current_user.id, campaign_id)
    return {"campaign_id": campaign_id, "count": len(jobs), "jobs": jobs}


@router.get("/{campaign_id}/publishing-jobs")
@log_calls
def list_publishing_jobs(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
):
    jobs = campaign_service.get_publishing_jobs(current_user.id, campaign_id)
    if jobs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return {"campaign_id": campaign_id, "count": len(jobs), "jobs": jobs}
