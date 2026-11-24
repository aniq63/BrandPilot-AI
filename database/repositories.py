from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from database.models import (
    AssetAssignment,
    AssetRequirement,
    Campaign,
    CampaignAsset,
    CampaignPost,
    PreparedPost,
    PublishingJob,
    StartupMarketingData,
)


class CampaignRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_owned_project(
        self,
        project_id: int,
        user_id: int,
    ) -> Optional[StartupMarketingData]:
        return (
            self.db.query(StartupMarketingData)
            .filter(
                StartupMarketingData.id == project_id,
                StartupMarketingData.user_id == user_id,
            )
            .first()
        )

    def get_campaign(
        self,
        campaign_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[Campaign]:
        query = self.db.query(Campaign)
        if user_id is not None:
            query = query.join(
                StartupMarketingData,
                Campaign.project_id == StartupMarketingData.id,
            ).filter(StartupMarketingData.user_id == user_id)
        return query.filter(Campaign.id == campaign_id).first()

    def create_campaign(
        self,
        project_id: int,
        name: str,
        strategy_snapshot: dict[str, Any],
        status: str = "draft",
    ) -> Campaign:
        campaign = Campaign(
            project_id=project_id,
            name=name,
            status=status,
            strategy_snapshot=strategy_snapshot,
        )
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        return campaign

    def set_campaign_status(self, campaign_id: int, status: str) -> None:
        self.db.query(Campaign).filter(Campaign.id == campaign_id).update(
            {"status": status}
        )
        self.db.commit()

    def replace_campaign_posts(
        self,
        campaign_id: int,
        posts: list[dict[str, Any]],
    ) -> Campaign:
        self.db.query(CampaignPost).filter(
            CampaignPost.campaign_id == campaign_id
        ).delete(synchronize_session=False)
        self.db.flush()

        for position, post in enumerate(posts):
            campaign_post = CampaignPost(
                campaign_id=campaign_id,
                position=post.get("position", position),
                topic=post["topic"],
                objective=post.get("objective"),
                format=post.get("format"),
                platform=post["platform"],
                caption_direction=post.get("caption_direction"),
                scheduled_at=post.get("scheduled_at"),
            )
            for req_position, requirement in enumerate(post.get("requirements", [])):
                campaign_post.requirements.append(
                    AssetRequirement(
                        media_type=requirement["media_type"],
                        description=requirement["description"],
                        position=requirement.get("position", req_position),
                        quantity=requirement.get("quantity", 1),
                        required=requirement.get("required", True),
                    )
                )
            self.db.add(campaign_post)

        self.db.commit()
        return self.get_campaign(campaign_id)

    def get_posts(self, campaign_id: int) -> list[CampaignPost]:
        return (
            self.db.query(CampaignPost)
            .filter(CampaignPost.campaign_id == campaign_id)
            .order_by(CampaignPost.position.asc(), CampaignPost.id.asc())
            .all()
        )

    def get_post(
        self,
        post_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[CampaignPost]:
        query = self.db.query(CampaignPost).join(
            Campaign, CampaignPost.campaign_id == Campaign.id
        )
        if user_id is not None:
            query = query.join(
                StartupMarketingData, Campaign.project_id == StartupMarketingData.id
            ).filter(StartupMarketingData.user_id == user_id)
        return query.filter(CampaignPost.id == post_id).first()

    def create_assets(
        self,
        project_id: int,
        campaign_id: Optional[int],
        uploaded_by: int,
        assets: list[dict[str, Any]],
    ) -> list[CampaignAsset]:
        created: list[CampaignAsset] = []
        for item in assets:
            asset = CampaignAsset(
                project_id=project_id,
                campaign_id=campaign_id,
                uploaded_by=uploaded_by,
                storage_path=item["storage_path"],
                public_url=item["public_url"],
                file_name=item["file_name"],
                mime_type=item["mime_type"],
                file_type=item["file_type"],
                size_bytes=item["size_bytes"],
                checksum=item.get("checksum"),
            )
            self.db.add(asset)
            created.append(asset)
        self.db.commit()
        for asset in created:
            self.db.refresh(asset)
        return created

    def get_asset(
        self,
        asset_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[CampaignAsset]:
        query = self.db.query(CampaignAsset)
        if user_id is not None:
            query = query.join(
                StartupMarketingData,
                CampaignAsset.project_id == StartupMarketingData.id,
            ).filter(StartupMarketingData.user_id == user_id)
        return query.filter(CampaignAsset.id == asset_id).first()

    def list_assets(
        self,
        project_id: int,
        campaign_id: Optional[int] = None,
    ) -> list[CampaignAsset]:
        query = self.db.query(CampaignAsset).filter(
            CampaignAsset.project_id == project_id
        )
        if campaign_id is not None:
            query = query.filter(CampaignAsset.campaign_id == campaign_id)
        return query.order_by(CampaignAsset.id.asc()).all()

    def delete_asset(self, asset: CampaignAsset) -> None:
        self.db.delete(asset)
        self.db.commit()

    def clear_assignments(self, campaign_id: int) -> None:
        post_ids = [
            post.id
            for post in self.db.query(CampaignPost)
            .filter(CampaignPost.campaign_id == campaign_id)
            .all()
        ]
        if not post_ids:
            return
        self.db.query(AssetAssignment).filter(
            AssetAssignment.post_id.in_(post_ids)
        ).delete(synchronize_session=False)
        self.db.commit()

    def replace_suggestions(
        self,
        campaign_id: int,
        suggestions: list[dict[str, Any]],
    ) -> list[AssetAssignment]:
        self.clear_assignments(campaign_id)
        created: list[AssetAssignment] = []
        for suggestion in suggestions:
            assignment = AssetAssignment(
                post_id=suggestion["post_id"],
                asset_id=suggestion["asset_id"],
                requirement_id=suggestion.get("requirement_id"),
                carousel_position=suggestion.get("carousel_position"),
                confidence=suggestion.get("confidence"),
                explanation=suggestion.get("explanation"),
                source=suggestion.get("source", "ai"),
                status=suggestion.get("status", "suggested"),
            )
            self.db.add(assignment)
            created.append(assignment)
        self.db.commit()
        for assignment in created:
            self.db.refresh(assignment)
        return created

    def get_assignment(
        self,
        assignment_id: int,
        campaign_id: int,
    ) -> Optional[AssetAssignment]:
        return (
            self.db.query(AssetAssignment)
            .join(CampaignPost, AssetAssignment.post_id == CampaignPost.id)
            .filter(
                AssetAssignment.id == assignment_id,
                CampaignPost.campaign_id == campaign_id,
            )
            .first()
        )

    def confirm_assignment(
        self,
        assignment: AssetAssignment,
        user_id: int,
        action: str,
        updates: dict[str, Any],
    ) -> AssetAssignment:
        assignment.status = action
        assignment.confirmed_by = user_id
        assignment.confirmed_at = datetime.now(timezone.utc)
        for field in ("asset_id", "requirement_id", "carousel_position"):
            if field in updates:
                setattr(assignment, field, updates[field])
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def add_manual_assignment(
        self,
        post_id: int,
        asset_id: int,
        requirement_id: Optional[int],
        user_id: int,
        carousel_position: Optional[int] = None,
    ) -> AssetAssignment:
        assignment = AssetAssignment(
            post_id=post_id,
            asset_id=asset_id,
            requirement_id=requirement_id,
            carousel_position=carousel_position,
            source="manual",
            status="accepted",
            confirmed_by=user_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def upsert_prepared_posts(
        self,
        campaign_id: int,
        drafts: list[dict[str, Any]],
    ) -> list[PreparedPost]:
        post_ids = {post.id for post in self.get_posts(campaign_id)}
        results: list[PreparedPost] = []
        for draft in drafts:
            post_id = draft["post_id"]
            if post_id not in post_ids:
                continue
            prepared = (
                self.db.query(PreparedPost)
                .filter(PreparedPost.post_id == post_id)
                .first()
            )
            if prepared is None:
                prepared = PreparedPost(post_id=post_id, platform=draft["platform"])
                self.db.add(prepared)
            prepared.platform = draft["platform"]
            prepared.caption = draft["caption"]
            prepared.hashtags = draft.get("hashtags", [])
            prepared.cta = draft.get("cta")
            prepared.content = draft.get("content", {})
            prepared.validation_notes = draft.get("validation_notes")
            prepared.status = draft.get("status", "draft")
            results.append(prepared)
        self.db.commit()
        for prepared in results:
            self.db.refresh(prepared)
        return results

    def get_prepared_post(
        self,
        prepared_post_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[PreparedPost]:
        query = (
            self.db.query(PreparedPost)
            .join(CampaignPost, PreparedPost.post_id == CampaignPost.id)
            .join(Campaign, CampaignPost.campaign_id == Campaign.id)
        )
        if user_id is not None:
            query = query.join(
                StartupMarketingData, Campaign.project_id == StartupMarketingData.id
            ).filter(StartupMarketingData.user_id == user_id)
        return query.filter(PreparedPost.id == prepared_post_id).first()

    def approve_prepared_post(
        self,
        prepared: PreparedPost,
        user_id: int,
    ) -> PreparedPost:
        prepared.status = "approved"
        prepared.approved_by = user_id
        prepared.approved_at = datetime.now(timezone.utc)
        prepared.post.status = "approved"
        self.db.commit()
        self.db.refresh(prepared)
        return prepared

    def request_revision(
        self,
        prepared: PreparedPost,
        note: str,
    ) -> PreparedPost:
        prepared.status = "revision_requested"
        prepared.validation_notes = note
        prepared.post.status = "revision_requested"
        self.db.commit()
        self.db.refresh(prepared)
        return prepared

    def create_publishing_jobs(
        self,
        prepared_posts: list[PreparedPost],
        connected_accounts: dict[str, dict[str, Any]],
    ) -> list[PublishingJob]:
        created: list[PublishingJob] = []
        for prepared in prepared_posts:
            if prepared.status != "approved":
                continue
            idempotency_key = f"publish:{prepared.id}"
            existing = (
                self.db.query(PublishingJob)
                .filter(PublishingJob.idempotency_key == idempotency_key)
                .first()
            )
            if existing is not None:
                created.append(existing)
                continue
            account = connected_accounts.get(prepared.platform.lower()) or connected_accounts.get(prepared.platform)
            if not account:
                raise ValueError(
                    f"No publishing-ready account is connected for {prepared.platform}."
                )
            scheduled_at = prepared.post.scheduled_at or datetime.now(timezone.utc)
            token_expires_at = account.get("token_expires_at")
            if isinstance(token_expires_at, str):
                try:
                    token_expires_at = datetime.fromisoformat(
                        token_expires_at.replace("Z", "+00:00")
                    )
                except ValueError:
                    token_expires_at = None
            job = PublishingJob(
                prepared_post_id=prepared.id,
                project_id=prepared.post.campaign.project_id,
                platform=prepared.platform,
                connected_account_id=account.get("connected_account_id"),
                platform_account_id=account.get("platform_account_id"),
                connection_status=account.get("connection_status"),
                publishing_scopes=account.get("publishing_scopes", []),
                token_expires_at=token_expires_at if isinstance(token_expires_at, datetime) else None,
                scheduled_at=scheduled_at,
                idempotency_key=idempotency_key,
                status="scheduled",
            )
            self.db.add(job)
            created.append(job)
        self.db.commit()
        for job in created:
            self.db.refresh(job)
        return created

    def list_publishing_jobs(self, campaign_id: int) -> list[PublishingJob]:
        return (
            self.db.query(PublishingJob)
            .join(PreparedPost, PublishingJob.prepared_post_id == PreparedPost.id)
            .join(CampaignPost, PreparedPost.post_id == CampaignPost.id)
            .filter(CampaignPost.campaign_id == campaign_id)
            .order_by(PublishingJob.id.asc())
            .all()
        )
