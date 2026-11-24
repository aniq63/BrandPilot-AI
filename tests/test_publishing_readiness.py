import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pydantic import ValidationError

from src.routes.schemas import SocialMediaAccountRequest
from src.services.campaign_service import _connected_account_map


READY_ACCOUNT = {
    "platform": "LinkedIn",
    "username": "brand",
    "profile_url": "https://linkedin.com/company/brand",
    "connected_account_id": "connection-123",
    "platform_account_id": "page-123",
    "connection_status": "connected",
    "publishing_enabled": True,
    "publishing_scopes": ["publish_content"],
}


class PublishingReadinessTests(unittest.TestCase):
    def test_publishing_enabled_requires_connection_details(self):
        payload = dict(READY_ACCOUNT)
        payload.pop("platform_account_id")
        with self.assertRaises(ValidationError):
            SocialMediaAccountRequest(**payload)

    def test_publishing_disabled_does_not_require_connection_details(self):
        payload = {
            "platform": "LinkedIn",
            "username": "brand",
            "profile_url": "https://linkedin.com/company/brand",
            "publishing_enabled": False,
        }
        account = SocialMediaAccountRequest(**payload)
        self.assertFalse(account.publishing_enabled)

    def test_connected_account_map_only_includes_ready_accounts(self):
        project = SimpleNamespace(
            social_media_accounts=[
                READY_ACCOUNT,
                {
                    "platform": "Instagram",
                    "username": "brand",
                    "profile_url": "https://instagram.com/brand",
                    "connected_account_id": "connection-456",
                    "publishing_enabled": True,
                    "connection_status": "connected",
                    "publishing_scopes": ["publish_content"],
                },
            ]
        )
        mapping = _connected_account_map(project)
        self.assertEqual(list(mapping), ["linkedin"])
        self.assertEqual(mapping["linkedin"]["platform_account_id"], "page-123")


if __name__ == "__main__":
    unittest.main(verbosity=2)
