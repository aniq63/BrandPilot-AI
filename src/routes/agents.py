import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.crud import (
    OUTPUT_COLUMNS,
    create_startup_data,
    get_startup_data,
    list_user_projects,
)
from database.models import StartupMarketingData, User
from src.routes.deps import get_current_user, get_db
from src.routes.runner import resume_workflow, start_workflow
from src.routes.schemas import (
    ReviewRequest,
    RunAcceptedResponse,
    RunStatusResponse,
    RunSummaryResponse,
    StartupDataRequest,
)

router = APIRouter(prefix="/agents", tags=["agents"])


def _owned_project(
    db: Session,
    project_id: int,
    user_id: int,
) -> StartupMarketingData:
    project = get_startup_data(db, project_id, user_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project


def _outputs(project: StartupMarketingData) -> dict[str, Any]:
    return {
        column: getattr(project, column)
        for column in OUTPUT_COLUMNS
        if getattr(project, column) is not None
    }


@router.post(
    "/runs",
    response_model=RunAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_startup_data(
    payload: StartupDataRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    thread_id = str(uuid.uuid4())
    startup_data = payload.model_dump(mode="json")

    project = create_startup_data(
        db=db,
        user_id=current_user.id,
        payload=startup_data,
        thread_id=thread_id,
    )

    background_tasks.add_task(
        start_workflow,
        project.id,
        thread_id,
        current_user.id,
        startup_data,
    )

    return RunAcceptedResponse(
        project_id=project.id,
        thread_id=thread_id,
        workflow_status=project.workflow_status,
        message="Agents started. Poll GET /agents/runs/{project_id} for progress.",
    )


@router.get("/runs", response_model=list[RunSummaryResponse])
def list_runs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    projects = list_user_projects(db, current_user.id)
    return [
        RunSummaryResponse(
            project_id=project.id,
            startup_name=project.startup_name,
            workflow_status=project.workflow_status,
            thread_id=project.thread_id,
        )
        for project in projects
    ]


@router.get("/runs/{project_id}", response_model=RunStatusResponse)
def get_run(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _owned_project(db, project_id, current_user.id)
    return RunStatusResponse(
        project_id=project.id,
        thread_id=project.thread_id,
        workflow_status=project.workflow_status,
        outputs=_outputs(project),
    )


@router.post(
    "/runs/{project_id}/review",
    response_model=RunAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def review_strategy(
    project_id: int,
    payload: ReviewRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _owned_project(db, project_id, current_user.id)
    if project.workflow_status != "awaiting_review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This project is not waiting for founder review",
        )

    review: dict[str, Any] = {"decision": payload.decision}
    if payload.feedback:
        review["feedback"] = payload.feedback

    background_tasks.add_task(
        resume_workflow,
        project.id,
        project.thread_id,
        review,
    )

    return RunAcceptedResponse(
        project_id=project.id,
        thread_id=project.thread_id,
        workflow_status="running",
        message="Founder review submitted. Agents are continuing.",
    )
