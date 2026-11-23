from typing import Any, Iterable

from langgraph.types import Command

from database.connection import SessionLocal
from database.crud import update_agent_outputs, update_workflow_status
from src.agents.graph.workflow import app

OUTPUT_KEYS = (
    "agent_startup_analysis",
    "agent_market_research",
    "agent_customer_research",
    "agent_social_media_strategy",
    "strategy_feedback",
)


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _persist_outputs(project_id: int, outputs: dict[str, Any]) -> None:
    if not outputs:
        return
    with SessionLocal() as db:
        update_agent_outputs(db, project_id, outputs)


def _persist_status(project_id: int, status: str) -> None:
    with SessionLocal() as db:
        update_workflow_status(db, project_id, status)


def _consume(stream: Iterable[dict], project_id: int) -> dict[str, Any]:
    saved: dict[str, Any] = {}
    for event in stream:
        updates = {}
        for value in event.values():
            if isinstance(value, dict):
                for key in OUTPUT_KEYS:
                    if key in value:
                        updates[key] = value[key]
        if updates:
            _persist_outputs(project_id, updates)
            saved.update(updates)
    return saved


def _finalize(project_id: int, thread_id: str) -> None:
    snapshot = app.get_state(_config(thread_id))
    status = "awaiting_review" if snapshot.interrupts else "completed"
    _persist_status(project_id, status)


def start_workflow(
    project_id: int,
    thread_id: str,
    user_id: int,
    startup_data: dict[str, Any],
) -> None:
    initial_state = {
        "user_id": user_id,
        "project_id": project_id,
        "thread_id": thread_id,
        **startup_data,
    }
    try:
        _consume(
            app.stream(initial_state, config=_config(thread_id), stream_mode="updates"),
            project_id,
        )
        _finalize(project_id, thread_id)
    except Exception:
        _persist_status(project_id, "failed")
        raise


def resume_workflow(
    project_id: int,
    thread_id: str,
    review: dict[str, Any],
) -> None:
    try:
        _consume(
            app.stream(
                Command(resume=review),
                config=_config(thread_id),
                stream_mode="updates",
            ),
            project_id,
        )
        _finalize(project_id, thread_id)
    except Exception:
        _persist_status(project_id, "failed")
        raise
