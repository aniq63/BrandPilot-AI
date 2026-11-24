import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api";
import StatusPill from "../components/StatusPill";
import { ArrowIcon, CheckIcon, RefreshIcon, UploadIcon } from "../components/Icons";

const TABS = [
  ["overview", "Overview"],
  ["assets", "Assets & mapping"],
  ["content", "Content drafts"],
  ["publishing", "Publishing"],
];

const formatDate = (value) => {
  if (!value) return "Flexible";
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

function AssetThumb({ asset, size = 54 }) {
  if (!asset) return <div className="asset-thumb placeholder" style={{ width: size, height: size }}>?</div>;
  return (
    <img
      className="asset-thumb"
      style={{ width: size, height: size }}
      src={asset.public_url}
      alt={asset.file_name}
      onError={(event) => {
        event.currentTarget.style.display = "none";
      }}
    />
  );
}

export default function Campaign() {
  const { campaignId } = useParams();
  const [campaign, setCampaign] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [activeTab, setActiveTab] = useState("overview");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [files, setFiles] = useState([]);
  const [decisions, setDecisions] = useState({});
  const [revisions, setRevisions] = useState({});
  const [manual, setManual] = useState({ post_id: "", asset_id: "", requirement_id: "", carousel_position: "" });
  const [busy, setBusy] = useState("");

  const load = useCallback(async () => {
    try {
      const [campaignData, suggestionData, jobData] = await Promise.all([
        api.getCampaign(campaignId),
        api.getAssetSuggestions(campaignId),
        api.listPublishingJobs(campaignId),
      ]);
      setCampaign(campaignData);
      setSuggestions(suggestionData.suggestions || []);
      setJobs(jobData.jobs || []);
      setDecisions((current) => {
        const next = {};
        (suggestionData.suggestions || []).forEach((assignment) => {
          next[assignment.id] = current[assignment.id] || {
            action: "accepted",
            asset_id: assignment.asset_id,
            requirement_id: assignment.requirement_id || "",
            carousel_position: assignment.carousel_position ?? "",
          };
        });
        return next;
      });
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }, [campaignId]);

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 4000);
    return () => window.clearInterval(timer);
  }, [load]);

  const run = async (key, action, message, after) => {
    setBusy(key);
    setNotice("");
    setError("");
    try {
      await action();
      setNotice(message);
      if (after) await after();
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy("");
    }
  };

  const uploadAssets = (event) => {
    event.preventDefault();
    if (!files.length) {
      setError("Select at least one image first.");
      return;
    }
    const data = new FormData();
    files.forEach((file) => data.append("files", file));
    run("upload", () => api.uploadCampaignAssets(campaignId, data), `${files.length} asset(s) uploaded.`, () => setFiles([]));
  };

  const setDecision = (id, key, value) => {
    setDecisions((current) => ({
      ...current,
      [id]: { ...(current[id] || {}), [key]: value },
    }));
  };

  const confirm = () => {
    const payload = Object.entries(decisions).map(([id, decision]) => ({
      assignment_id: Number(id),
      action: decision.action,
      asset_id: Number(decision.asset_id) || undefined,
      requirement_id: decision.requirement_id ? Number(decision.requirement_id) : undefined,
      carousel_position:
        decision.carousel_position === "" || decision.carousel_position === undefined
          ? undefined
          : Number(decision.carousel_position),
    }));
    if (!payload.length) {
      setError("No suggestions available to confirm.");
      return;
    }
    run("confirm", () => api.confirmAssignments(campaignId, { confirmations: payload }), "Asset mapping confirmed.");
  };

  const addManual = (event) => {
    event.preventDefault();
    if (!manual.post_id || !manual.asset_id) {
      setError("Choose a post and an asset.");
      return;
    }
    run(
      "manual",
      () =>
        api.addManualAssignment(campaignId, {
          post_id: Number(manual.post_id),
          asset_id: Number(manual.asset_id),
          requirement_id: manual.requirement_id ? Number(manual.requirement_id) : undefined,
          carousel_position: manual.carousel_position === "" ? undefined : Number(manual.carousel_position),
        }),
      "Manual assignment added.",
      () => setManual({ post_id: "", asset_id: "", requirement_id: "", carousel_position: "" }),
    );
  };

  const reviewPost = async (preparedId, decision, note) => {
    if (decision === "revision" && !note?.trim()) {
      setError("Add a revision note for this post.");
      return;
    }
    await run(
      `post-${preparedId}`,
      () => api.reviewPreparedPost(preparedId, { decision, note: note?.trim() || undefined }),
      decision === "approve" ? "Post approved." : "Revision requested.",
      () => setRevisions((current) => ({ ...current, [preparedId]: "" })),
    );
  };

  if (!campaign) {
    return (
      <section className="page-section">
        <div className="container">
          <div className="empty-state"><div className="spinner" /><p>Loading campaign…</p></div>
          {error && <div className="alert alert-error">{error}</div>}
        </div>
      </section>
    );
  }

  const assetsById = Object.fromEntries((campaign.assets || []).map((asset) => [asset.id, asset]));
  const posts = campaign.posts || [];
  const suggestionsByPost = posts.map((post) => ({
    post,
    items: suggestions.filter((assignment) => assignment.post_id === post.id),
  }));

  return (
    <section className="page-section">
      <div className="container">
        <div className="page-heading">
          <div>
            <span className="eyebrow">Campaign #{campaign.id}</span>
            <h1>{campaign.name}</h1>
            <p>
              {campaign.start_date || "Flexible start"} → {campaign.end_date || "Flexible end"} · {posts.length} posts
            </p>
          </div>
          <div className="heading-actions">
            <StatusPill value={campaign.status} />
            <Link to={`/runs/${campaign.project_id}`} className="btn btn-ghost">Back to strategy</Link>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {notice && <div className="alert alert-success">{notice}</div>}

        <div className="tab-bar">
          {TABS.map(([key, label]) => (
            <button
              type="button"
              key={key}
              className={activeTab === key ? "active" : ""}
              onClick={() => setActiveTab(key)}
            >
              {label}
            </button>
          ))}
        </div>

        {activeTab === "overview" && (
          <div className="content-grid">
            <div className="panel">
              <div className="panel-head"><h2>Campaign objectives</h2></div>
              <div className="tag-list">
                {(campaign.objectives || []).map((objective, index) => (
                  <span className="tag" key={index}>{objective}</span>
                ))}
              </div>
            </div>
            <div className="panel">
              <div className="panel-head"><h2>Posting calendar</h2><span>{posts.length} planned</span></div>
              <div className="calendar-list">
                {posts.map((post) => (
                  <article className="calendar-item" key={post.id}>
                    <span className="calendar-date">{new Date(post.scheduled_at || Date.now()).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</span>
                    <div className="calendar-body">
                      <div className="calendar-title">
                        <strong>{post.topic}</strong>
                        <StatusPill value={post.status} />
                      </div>
                      <p>{post.objective}</p>
                      <div className="calendar-meta">
                        <span>{post.platform}</span>
                        <span>{post.format}</span>
                        <span>{formatDate(post.scheduled_at)}</span>
                      </div>
                      <div className="tag-list small">
                        {post.requirements.map((requirement) => (
                          <span className="tag subtle" key={requirement.id}>
                            {requirement.media_type}: {requirement.description}
                          </span>
                        ))}
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === "assets" && (
          <div className="content-grid">
            <div className="panel">
              <div className="panel-head">
                <h2>Bulk upload assets</h2>
                <span>{campaign.assets.length} available</span>
              </div>
              <form className="upload-form" onSubmit={uploadAssets}>
                <label className="dropzone">
                  <UploadIcon />
                  <strong>Choose campaign images</strong>
                  <span>JPG, PNG, WEBP or GIF · max 10 MB each</span>
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={(event) => setFiles(Array.from(event.target.files || []))}
                  />
                </label>
                {files.length > 0 && <p className="selected-files">{files.length} file(s) selected</p>}
                <button className="btn btn-primary" type="submit" disabled={busy === "upload"}>
                  {busy === "upload" ? "Uploading…" : "Upload assets"}
                </button>
              </form>
              <div className="asset-grid">
                {campaign.assets.map((asset) => (
                  <div className="asset-card" key={asset.id}>
                    <AssetThumb asset={asset} size={72} />
                    <div><strong>{asset.file_name}</strong><p>{asset.file_type} · {Math.round(asset.size_bytes / 1024)} KB</p></div>
                  </div>
                ))}
              </div>
              <div className="inline-actions">
                <button
                  className="btn btn-outline"
                  type="button"
                  disabled={busy === "suggest"}
                  onClick={() => run("suggest", () => api.requestAssetSuggestions(campaignId), "AI asset analysis started.")}
                >
                  Analyze & suggest assets
                </button>
                <button
                  className="btn btn-ghost"
                  type="button"
                  disabled={busy === "regenerate-assets"}
                  onClick={() => run("regenerate-assets", () => api.regenerateAssetSuggestions(campaignId), "Suggestions will be regenerated.")}
                >
                  <RefreshIcon /> Regenerate suggestions
                </button>
              </div>
            </div>

            <div className="panel">
              <div className="panel-head">
                <h2>AI asset suggestions</h2>
                <span>{suggestions.length} suggestions</span>
              </div>
              {suggestionsByPost.map(({ post, items }) => (
                <div className="suggestion-group" key={post.id}>
                  <h3>{post.topic} <span>{post.platform}</span></h3>
                  {items.length === 0 ? (
                    <p className="muted">No suggestions yet for this post.</p>
                  ) : (
                    items.map((assignment) => {
                      const decision = decisions[assignment.id] || {};
                      return (
                        <div className="suggestion-row" key={assignment.id}>
                          <AssetThumb asset={assetsById[assignment.asset_id]} />
                          <div className="suggestion-copy">
                            <strong>{assetsById[assignment.asset_id]?.file_name || `Asset #${assignment.asset_id}`}</strong>
                            <p>{assignment.explanation}</p>
                            <small>Confidence {Math.round((assignment.confidence || 0) * 100)}%</small>
                            <select
                              value={decision.asset_id ?? assignment.asset_id}
                              onChange={(event) => setDecision(assignment.id, "asset_id", Number(event.target.value))}
                            >
                              {campaign.assets.map((asset) => (
                                <option value={asset.id} key={asset.id}>{asset.file_name}</option>
                              ))}
                            </select>
                            <input
                              type="number"
                              min="0"
                              placeholder="Carousel position"
                              value={decision.carousel_position ?? ""}
                              onChange={(event) => setDecision(assignment.id, "carousel_position", event.target.value)}
                            />
                          </div>
                          <div className="decision-toggle">
                            <button
                              type="button"
                              className={decision.action !== "rejected" ? "active" : ""}
                              onClick={() => setDecision(assignment.id, "action", "accepted")}
                            >
                              <CheckIcon /> Use
                            </button>
                            <button
                              type="button"
                              className={decision.action === "rejected" ? "active danger" : ""}
                              onClick={() => setDecision(assignment.id, "action", "rejected")}
                            >
                              Skip
                            </button>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              ))}
              <div className="confirm-bar">
                <button className="btn btn-pink" type="button" disabled={busy === "confirm"} onClick={confirm}>
                  Confirm asset mapping <ArrowIcon />
                </button>
                <span>Posts are not finalized until you confirm.</span>
              </div>
            </div>

            <div className="panel panel-wide">
              <div className="panel-head"><h2>Add an asset manually</h2><span>Optional override</span></div>
              <form className="manual-form" onSubmit={addManual}>
                <select value={manual.post_id} onChange={(event) => setManual({ ...manual, post_id: event.target.value })}>
                  <option value="">Choose post</option>
                  {posts.map((post) => <option value={post.id} key={post.id}>{post.topic}</option>)}
                </select>
                <select value={manual.asset_id} onChange={(event) => setManual({ ...manual, asset_id: event.target.value })}>
                  <option value="">Choose asset</option>
                  {campaign.assets.map((asset) => <option value={asset.id} key={asset.id}>{asset.file_name}</option>)}
                </select>
                <select value={manual.requirement_id} onChange={(event) => setManual({ ...manual, requirement_id: event.target.value })}>
                  <option value="">No requirement</option>
                  {posts.flatMap((post) => post.requirements).map((requirement) => (
                    <option value={requirement.id} key={requirement.id}>{requirement.description}</option>
                  ))}
                </select>
                <input
                  type="number"
                  min="0"
                  placeholder="Carousel position"
                  value={manual.carousel_position}
                  onChange={(event) => setManual({ ...manual, carousel_position: event.target.value })}
                />
                <button className="btn btn-outline" type="submit" disabled={busy === "manual"}>Add assignment</button>
              </form>
            </div>
          </div>
        )}

        {activeTab === "content" && (
          <div className="panel">
            <div className="panel-head">
              <h2>Ready-to-review posts</h2>
              <div className="inline-actions">
                <button
                  className="btn btn-primary"
                  type="button"
                  disabled={busy === "content"}
                  onClick={() => run("content", () => api.prepareContent(campaignId), "Content preparation started.")}
                >
                  Prepare content
                </button>
                <button
                  className="btn btn-ghost"
                  type="button"
                  disabled={busy === "regen-content"}
                  onClick={() => run("regen-content", () => api.regenerateContent(campaignId), "Drafts will be regenerated.")}
                >
                  <RefreshIcon /> Regenerate all
                </button>
              </div>
            </div>
            <div className="draft-list">
              {posts.map((post) => {
                const prepared = post.prepared_post;
                return (
                  <article className="draft-card" key={post.id}>
                    <div className="draft-head">
                      <div><strong>{post.topic}</strong><p>{post.platform} · {formatDate(post.scheduled_at)}</p></div>
                      <StatusPill value={prepared?.status || post.status} />
                    </div>
                    {prepared ? (
                      <>
                        <p className="draft-caption">{prepared.caption}</p>
                        <div className="draft-meta">
                          <div><small>Hashtags</small><div className="tag-list small">{(prepared.hashtags || []).map((tag, index) => <span className="tag subtle" key={index}>{tag}</span>)}</div></div>
                          <div><small>Call to action</small><p>{prepared.cta || "Not specified"}</p></div>
                        </div>
                        {post.assignments.filter((assignment) => assignment.status === "accepted").length > 0 && (
                          <div className="draft-assets">
                            {post.assignments
                              .filter((assignment) => assignment.status === "accepted")
                              .map((assignment) => {
                                const asset = assetsById[assignment.asset_id];
                                return asset ? <AssetThumb asset={asset} key={assignment.id} size={46} /> : null;
                              })}
                          </div>
                        )}
                        {prepared.validation_notes && <p className="draft-note">{prepared.validation_notes}</p>}
                        <div className="draft-actions">
                          <button
                            className="btn btn-primary btn-small"
                            type="button"
                            disabled={busy === `post-${prepared.id}`}
                            onClick={() => reviewPost(prepared.id, "approve")}
                          >
                            Approve post
                          </button>
                          <textarea
                            rows={2}
                            placeholder="What should change?"
                            value={revisions[prepared.id] || ""}
                            onChange={(event) => setRevisions({ ...revisions, [prepared.id]: event.target.value })}
                          />
                          <button
                            className="btn btn-outline btn-small"
                            type="button"
                            disabled={busy === `post-${prepared.id}`}
                            onClick={() => reviewPost(prepared.id, "revision", revisions[prepared.id])}
                          >
                            Request revision
                          </button>
                        </div>
                      </>
                    ) : (
                      <p className="muted">No draft yet. Prepare content to generate one.</p>
                    )}
                  </article>
                );
              })}
            </div>
          </div>
        )}

        {activeTab === "publishing" && (
          <div className="panel">
            <div className="panel-head">
              <div>
                <h2>Publishing jobs</h2>
                <p>Only approved posts can become jobs. Nothing is published automatically.</p>
              </div>
              <button
                className="btn btn-primary"
                type="button"
                disabled={busy === "jobs"}
                onClick={() => run("jobs", () => api.createPublishingJobs(campaignId), "Publishing jobs created.")}
              >
                Create jobs
              </button>
            </div>
            {jobs.length === 0 ? (
              <div className="empty-state small">
                <h3>No jobs yet</h3>
                <p>Approve posts in the Content drafts tab, then create publishing jobs.</p>
              </div>
            ) : (
              <div className="job-table">
                <div className="job-row job-header"><span>Post</span><span>Platform</span><span>Scheduled</span><span>Status</span><span>Account</span></div>
                {jobs.map((job) => {
                  const prepared = posts.find((post) => post.prepared_post?.id === job.prepared_post_id)?.prepared_post;
                  return (
                    <div className="job-row" key={job.id}>
                      <span>{prepared?.caption?.slice(0, 42) || `Prepared #${job.prepared_post_id}`}…</span>
                      <span>{job.platform}</span>
                      <span>{formatDate(job.scheduled_at)}</span>
                      <span><StatusPill value={job.status} /></span>
                      <span>{job.connected_account_id || "Not connected"}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
