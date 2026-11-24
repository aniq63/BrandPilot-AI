import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.crud import _serialize_json_output, _serialize_text_output
from src.agents.graph.nodes import _response_text


CONTENT_BLOCKS = [
    {"type": "text", "text": "First section"},
    {"type": "text", "text": "Second section"},
]


class AgentOutputSerializationTests(unittest.TestCase):
    def test_response_text_flattens_content_blocks(self):
        response = SimpleNamespace(content=CONTENT_BLOCKS)
        self.assertEqual(_response_text(response), "First section\nSecond section")

    def test_serialize_text_output_accepts_content_blocks(self):
        self.assertEqual(
            _serialize_text_output(CONTENT_BLOCKS),
            "First section\nSecond section",
        )

    def test_serialize_text_output_preserves_none(self):
        self.assertIsNone(_serialize_text_output(None))

    def test_serialize_json_output_parses_json_string(self):
        self.assertEqual(_serialize_json_output('{"campaign_objective": "launch"}'), {"campaign_objective": "launch"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
