import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.crud import STARTUP_INPUT_FIELDS
from src.routes import runner


class RetryWorkflowTests(unittest.TestCase):
    @patch("src.routes.runner.SessionLocal")
    @patch("src.routes.runner._finalize")
    @patch("src.routes.runner.app.stream")
    @patch("src.routes.runner.app.get_state")
    def test_retry_resumes_from_checkpoint(
        self,
        get_state,
        stream,
        finalize,
        session_local,
    ):
        get_state.return_value = SimpleNamespace(
            next=("market_research",),
            values={},
            interrupts=None,
        )
        stream.return_value = []

        runner.retry_workflow(1, "thread-1", 1)

        stream.assert_called_once()
        self.assertIsNone(stream.call_args.args[0])
        finalize.assert_called_once()

    @patch("src.routes.runner.start_workflow")
    @patch("src.routes.runner.SessionLocal")
    @patch("src.routes.runner.app.get_state")
    def test_retry_restarts_without_checkpoint(
        self,
        get_state,
        session_local,
        start_workflow,
    ):
        get_state.return_value = SimpleNamespace(
            next=(),
            values={},
            interrupts=None,
        )
        db = MagicMock()
        project = SimpleNamespace(
            **{field: f"value-{field}" for field in STARTUP_INPUT_FIELDS}
        )
        db.query.return_value.filter_by.return_value.first.return_value = project
        session_local.return_value.__enter__.return_value = db

        runner.retry_workflow(1, "thread-1", 1)

        start_workflow.assert_called_once()
        startup_data = start_workflow.call_args.args[3]
        self.assertEqual(startup_data["startup_name"], "value-startup_name")


if __name__ == "__main__":
    unittest.main(verbosity=2)
