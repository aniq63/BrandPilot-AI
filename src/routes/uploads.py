from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from database.crud import get_startup_data, update_brand_media
from database.models import User
from src.routes.deps import get_current_user, get_db
from src.routes.schemas import BrandUploadResponse
from src.services.supabase_storage import upload_brand_image

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/brand", response_model=BrandUploadResponse)
async def upload_brand_media(
    brand_logo: Annotated[Optional[UploadFile], File()] = None,
    brand_images: Annotated[Optional[list[UploadFile]], File()] = None,
    project_id: Annotated[Optional[int], Form()] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if brand_logo is None and not brand_images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide a brand logo or at least one brand image",
        )

    if project_id is not None:
        project = get_startup_data(db, project_id, current_user.id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

    logo_url = None
    asset_urls = []

    try:
        if brand_logo is not None:
            content = await brand_logo.read()
            logo_url = await run_in_threadpool(
                upload_brand_image,
                user_id=current_user.id,
                project_id=project_id,
                filename=brand_logo.filename or "logo",
                content=content,
                content_type=brand_logo.content_type or "image/png",
                folder="logo",
            )

        for image in brand_images or []:
            content = await image.read()
            url = await run_in_threadpool(
                upload_brand_image,
                user_id=current_user.id,
                project_id=project_id,
                filename=image.filename or "image",
                content=content,
                content_type=image.content_type or "image/png",
                folder="assets",
            )
            asset_urls.append(url)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    finally:
        if brand_logo is not None:
            await brand_logo.close()
        for image in brand_images or []:
            await image.close()

    if project_id is not None:
        update_brand_media(
            db,
            project_id,
            brand_logo=logo_url,
            brand_assets=asset_urls,
        )

    return BrandUploadResponse(
        brand_logo=logo_url,
        brand_assets=asset_urls,
        project_id=project_id,
    )
