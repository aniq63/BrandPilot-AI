import sys
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.connection import SessionLocal
from database.crud import create_startup_data, create_user
from database.models import Campaign, CampaignAsset, PublishingJob
from src.services import campaign_service


class CampaignPipelineTests(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        self.user = create_user(
            self.db,
            username=f"campaign_test_{uuid.uuid4().hex[:8]}",
            email=f"campaign_{uuid.uuid4().hex}@example.com",
            password_hash="unused",
        )
        self.project = create_startup_data(
            self.db,
            self.user.id,
            {
                "startup_name": "Pipeline Test Startup",
                "website_url": "https://example.com",
                "product_name": "Pipeline Test Product",
                "product_description": "A product used for campaign pipeline tests.",
                "industry": "Software",
                "marketing_goals": ["brand awareness"],
                "campaign_duration": "2 weeks",
                "social_media_accounts": [
                    {
                        "platform": "LinkedIn",
                        "username": "test",
                        "profile_url": "https://linkedin.com/company/test",
                        "connected_account_id": "acc-123",
                        "platform_account_id": "page-123",
                        "connection_status": "connected",
                        "publishing_enabled": True,
                        "publishing_scopes": ["publish_content"],
                    }
                ],
                "brand_logo": "https://example.com/logo.png",
                "brand_assets": ["https://example.com/product.png"],
            },
            str(uuid.uuid4()),
        )
        self.project.agent_social_media_strategy = {
            "campaign_objective": "Build awareness",
            "selected_platforms": ["LinkedIn"],
            "content_pillars": ["Education"],
            "brand_voice": "Clear and practical",
        }
        self.db.commit()

    def tearDown(self):
        try:
            self.db.query(PublishingJob).filter(
                PublishingJob.project_id == self.project.id
            ).delete(synchronize_session=False)
            self.db.query(CampaignAsset).filter(
                CampaignAsset.project_id == self.project.id
            ).delete(synchronize_session=False)
            self.db.query(Campaign).filter(
                Campaign.project_id == self.project.id
            ).delete(synchronize_session=False)
            self.db.delete(self.project)
            self.db.delete(self.user)
            self.db.commit()
        finally:
            self.db.close()

    def test_full_campaign_pipeline_with_mocked_workflows(self):
        plan = {
            "name": "Awareness Campaign",
            "start_date": "2026-12-01",
            "end_date": "2026-12-14",
            "campaign_duration": "2 weeks",
            "objectives": ["Build awareness"],
            "posts": [
                {
                    "topic": "Product introduction",
                    "objective": "Introduce the product",
                    "format": "single image",
                    "platform": "LinkedIn",
                    "caption_direction": "Practical and concise",
                    "scheduled_at": "2026-12-01T09:00:00+00:00",
                    "requirements": [
                        {
                            "media_type": "image",
                            "description": "Product image",
                            "position": 0,
                            "quantity": 1,
                            "required": True,
                        }
                    ],
                }
            ],
        }

        with patch.object(
            campaign_service.campaign_orchestrator_app,
            "invoke",
            return_value={"plan": plan},
        ):
            campaign_id = campaign_service.start_campaign_orchestration(
                self.user.id,
                self.project.id,
            )
        self.assertIsNotNone(campaign_id)

        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        self.assertEqual(campaign.status, "assets_pending")
        self.assertEqual(len(campaign.posts), 1)
        self.assertEqual(len(campaign.posts[0].requirements), 1)
        self.assertEqual(len(campaign.assets), 2)

        asset = (
            self.db.query(CampaignAsset)
            .filter(CampaignAsset.project_id == self.project.id)
            .first()
        )
        requirement = campaign.posts[0].requirements[0]

        suggestion_result = {
            "suggestions": {
                "suggestions": [
                    {
                        "post_id": campaign.posts[0].id,
                        "asset_id": asset.id,
                        "requirement_id": requirement.id,
                        "carousel_position": 0,
                        "confidence": 0.9,
                        "explanation": "Relevant product asset",
                    }
                ],
                "unmet_requirements": [],
            }
        }
        with patch.object(
            campaign_service.asset_matching_app,
            "invoke",
            return_value=suggestion_result,
        ):
            suggestion_count = campaign_service.run_asset_matching(
                self.user.id,
                campaign_id,
            )
        self.assertEqual(suggestion_count, 1)

        details = campaign_service.get_campaign_details(self.user.id, campaign_id)
        assignment = details["posts"][0]["assignments"][0]
        self.assertEqual(assignment["status"], "suggested")

        confirmed = campaign_service.confirm_asset_assignments(
            self.user.id,
            campaign_id,
            [
                {
                    "assignment_id": assignment["id"],
                    "action": "accepted",
                }
            ],
        )
        self.assertEqual(confirmed, 1)

        draft_result = {
            "drafts": {
                "drafts": [
                    {
                        "post_id": campaign.posts[0].id,
                        "platform": "LinkedIn",
                        "caption": "Meet Pipeline Test Product.",
                        "hashtags": ["#SaaS"],
                        "cta": "Learn more",
                        "content": {"headline": "Product introduction"},
                        "validation_notes": "",
                    }
                ]
            }
        }
        with patch.object(
            campaign_service.content_preparation_app,
            "invoke",
            return_value=draft_result,
        ):
            draft_count = campaign_service.run_content_preparation(
                self.user.id,
                campaign_id,
            )
        self.assertEqual(draft_count, 1)

        details = campaign_service.get_campaign_details(self.user.id, campaign_id)
        prepared = details["posts"][0]["prepared_post"]
        self.assertIsNotNone(prepared)
        self.assertEqual(prepared["status"], "draft")

        approved = campaign_service.review_prepared_post(
            self.user.id,
            prepared["id"],
            "approve",
        )
        self.assertEqual(approved["status"], "approved")

        jobs = campaign_service.create_publishing_jobs(self.user.id, campaign_id)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["connected_account_id"], "acc-123")

        repeat_jobs = campaign_service.create_publishing_jobs(
            self.user.id,
            campaign_id,
        )
        self.assertEqual(len(repeat_jobs), 1)
        self.assertEqual(repeat_jobs[0]["id"], jobs[0]["id"])

        self.assertIsInstance(
            datetime.fromisoformat(jobs[0]["scheduled_at"]),
            datetime,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
