import threading
from typing import Any, Iterable, Optional

from langchain_core.callbacks import BaseCallbackHandler
from langgraph.types import Command

from database.connection import SessionLocal
from database.crud import (
    STARTUP_INPUT_FIELDS,
    update_agent_outputs,
    update_current_agents,
    update_workflow_status,
)
from database.models import StartupMarketingData
from src.agents.graph.workflow import app
from src.utilis.logging import logger, log_calls

OUTPUT_KEYS = (
    "agent_startup_analysis",
    "agent_market_research",
    "agent_customer_research",
    "agent_social_media_strategy",
    "strategy_feedback",
)

TRACKED_NODES = frozenset(
    {
        "startup_analysis",
        "market_research",
        "customer_research",
        "social_media_strategy",
        "strategy_review",
        "strategy_optimization",
        "campaign_orchestrator",
    }
)


class WorkflowProgressHandler(BaseCallbackHandler):
    def __init__(self, project_id: int) -> None:
        self.project_id = project_id
        self.active: dict[str, str] = {}
        self.lock = threading.Lock()

    @log_calls
    def on_chain_start(
        self,
        serialized: Optional[dict[str, Any]],
        inputs: Any,
        *,
        run_id: Any,
        parent_run_id: Optional[Any] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        node = (metadata or {}).get("langgraph_node")
        if node not in TRACKED_NODES:
            return
        with self.lock:
            self.active[str(run_id)] = node
            self._persist()

    @log_calls
    def on_chain_end(
        self,
        outputs: Any,
        *,
        run_id: Any,
        parent_run_id: Optional[Any] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        self._finish(str(run_id))

    @log_calls
    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: Any,
        parent_run_id: Optional[Any] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        self._finish(str(run_id))

    @log_calls
    def clear(self) -> None:
        with self.lock:
            self.active.clear()
            self._persist()

    @log_calls
    def _finish(self, run_id: str) -> None:
        with self.lock:
            if run_id not in self.active:
                return
            del self.active[run_id]
            self._persist()

    @log_calls
    def _persist(self) -> None:
        current = sorted(set(self.active.values()))
        with SessionLocal() as db:
            update_current_agents(db, self.project_id, current or None)


@log_calls
def _config(thread_id: str, callbacks: Optional[list[BaseCallbackHandler]] = None) -> dict:
    config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    if callbacks:
        config["callbacks"] = callbacks
    return config


@log_calls
def _persist_outputs(project_id: int, outputs: dict[str, Any]) -> None:
    if not outputs:
        return
    with SessionLocal() as db:
        update_agent_outputs(db, project_id, outputs)


@log_calls
def _persist_status(project_id: int, status: str) -> None:
    with SessionLocal() as db:
        update_workflow_status(db, project_id, status)


@log_calls
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


@log_calls
def _finalize(project_id: int, thread_id: str) -> None:
    snapshot = app.get_state(_config(thread_id))
    status = "awaiting_review" if snapshot.interrupts else "completed"
    _persist_status(project_id, status)


@log_calls
def _run_stream(
    project_id: int,
    thread_id: str,
    payload: Any,
) -> None:
    handler = WorkflowProgressHandler(project_id)
    try:
        _consume(
            app.stream(
                payload,
                config=_config(thread_id, [handler]),
                stream_mode="updates",
            ),
            project_id,
        )
        _finalize(project_id, thread_id)
    except Exception:
        logger.exception("Workflow failed for project %s thread %s", project_id, thread_id)
        _persist_status(project_id, "failed")
        raise
    finally:
        handler.clear()


@log_calls
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
    _run_stream(project_id, thread_id, initial_state)


@log_calls
def resume_workflow(
    project_id: int,
    thread_id: str,
    review: dict[str, Any],
) -> None:
    _run_stream(project_id, thread_id, Command(resume=review))


@log_calls
def retry_workflow(
    project_id: int,
    thread_id: str,
    user_id: int,
) -> None:
    snapshot = app.get_state(_config(thread_id))
    if snapshot.next:
        _run_stream(project_id, thread_id, None)
        return

    with SessionLocal() as db:
        project = (
            db.query(StartupMarketingData)
            .filter_by(id=project_id, user_id=user_id)
            .first()
        )
        if project is None:
            raise LookupError("Project not found.")
        startup_data = {
            field: getattr(project, field)
            for field in STARTUP_INPUT_FIELDS
        }

    start_workflow(project_id, thread_id, user_id, startup_data)
