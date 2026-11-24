const LABELS = {
  pending: "Pending",
  running: "Running",
  awaiting_review: "Needs your review",
  completed: "Completed",
  failed: "Failed",
  draft: "Draft",
  assets_pending: "Waiting for assets",
  asset_analysis_ready: "Assets ready to confirm",
  assets_confirmed: "Assets confirmed",
  content_ready: "Content ready",
  publishing_scheduled: "Publishing scheduled",
  suggested: "Suggested",
  accepted: "Accepted",
  rejected: "Rejected",
  approved: "Approved",
  revision_requested: "Revision requested",
  planned: "Planned",
  scheduled: "Scheduled",
};

export default function StatusPill({ value }) {
  const key = (value || "pending").toLowerCase();
  const tone = key.includes("fail")
    ? "danger"
    : key.includes("await") || key.includes("review") || key.includes("revision")
      ? "warning"
      : key.includes("complete") || key.includes("approve") || key.includes("accept") || key.includes("scheduled")
        ? "success"
        : "info";

  return (
    <span className={`status-pill status-${tone}`}>
      <span className="status-dot" />
      {LABELS[key] || value || "Pending"}
    </span>
  );
}
