import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api";
import Markdown from "../components/Markdown";
import StatusPill from "../components/StatusPill";
import { ArrowIcon, ChartIcon, CheckIcon, ClockIcon, SparkIcon } from "../components/Icons";

const LIST_SECTIONS = [
  ["Selected platforms", "selected_platforms"],
  ["Content pillars", "content_pillars"],
  ["Content themes", "content_themes"],
  ["Hashtag strategy", "hashtag_strategy"],
  ["Calls to action", "call_to_action"],
  ["Success metrics", "success_metrics"],
  ["Expected outcomes", "expected_outcomes"],
  ["Recommendations", "recommendations"],
];

const OBJECT_SECTIONS = [
  ["Platform strategies", "platform_strategies"],
  ["Campaign ideas", "campaign_ideas"],
  ["Audience segments", "audience_segments"],
];

const AGENT_LABELS = {
  startup_analysis: "Startup analysis",
  market_research: "Market research",
  customer_research: "Customer research",
  social_media_strategy: "Social strategy",
  strategy_review: "Founder review",
  strategy_optimization: "Strategy optimization",
  campaign_orchestrator: "Campaign builder",
};

function ListItems({ items }) {
  if (!Array.isArray(items) || !items.length) return <p className="muted">Not specified.</p>;
  return (
    <div className="tag-list">
      {items.map((item, index) => (
        <span key={index} className="tag">{typeof item === "string" ? item : JSON.stringify(item)}</span>
      ))}
    </div>
  );
}

function ObjectItems({ items }) {
  if (!Array.isArray(items) || !items.length) return <p className="muted">Not specified.</p>;
  return (
    <div className="object-list">
      {items.map((item, index) => {
        const title = item?.title || item?.name || item?.platform || item?.segment || `Item ${index + 1}`;
        return (
          <div className="object-card" key={index}>
            <strong>{title}</strong>
            {Object.entries(item || {})
              .filter(([key]) => !["title", "name", "platform", "segment"].includes(key))
              .map(([key, value]) => (
                <p key={key}>
                  <span>{key.replaceAll("_", " ")}</span>
                  {typeof value === "object" ? JSON.stringify(value) : String(value)}
                </p>
              ))}
          </div>
        );
      })}
    </div>
  );
}

function StrategyView({ strategy }) {
  if (!strategy) return <p className="muted">The strategy will appear here when the agents finish.</p>;
  return (
    <div className="strategy-view">
      <div className="strategy-hero">
        <div>
          <small>Campaign objective</small>
          <h3>{strategy.campaign_objective || "Not specified"}</h3>
        </div>
        <div>
          <small>Duration</small>
          <h3>{strategy.campaign_duration || "Not specified"}</h3>
        </div>
      </div>

      <div className="strategy-text-grid">
        <div><small>Overall strategy</small><p>{strategy.overall_strategy || "Not specified"}</p></div>
        <div><small>Brand voice</small><p>{strategy.brand_voice || "Not specified"}</p></div>
        <div><small>Content frequency</small><p>{strategy.content_frequency || "Not specified"}</p></div>
        <div><small>Messaging strategy</small><p>{strategy.messaging_strategy || "Not specified"}</p></div>
      </div>

      <div className="strategy-list-grid">
        {LIST_SECTIONS.map(([title, key]) => (
          <div className="strategy-block" key={key}>
            <h4>{title}</h4>
            <ListItems items={strategy[key]} />
          </div>
        ))}
      </div>

      <div className="strategy-object-grid">
        {OBJECT_SECTIONS.map(([title, key]) => (
          <div className="strategy-block" key={key}>
            <h4>{title}</h4>
            <ObjectItems items={strategy[key]} />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ProjectRun() {
  const { projectId } = useParams();
  const [run, setRun] = useState(null);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState("");
  const [reviewBusy, setReviewBusy] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const retriedRef = useRef(false);

  const load = useCallback(async () => {
    try {
      const data = await api.getRun(projectId);
      setRun(data);
      setError("");

      if (data.workflow_status === "failed" && !retriedRef.current) {
        retriedRef.current = true;
        setRetrying(true);
        try {
          await api.retryRun(projectId);
          setRun(await api.getRun(projectId));
        } catch (err) {
          setError(err.message);
        } finally {
          setRetrying(false);
        }
      }
    } catch (err) {
      setError(err.message);
    }
  }, [projectId]);

  useEffect(() => {
    retriedRef.current = false;
    load();
    const timer = window.setInterval(load, 3000);
    return () => window.clearInterval(timer);
  }, [load]);

  const submitReview = async (decision) => {
    if (decision !== "approve" && !feedback.trim()) {
      setError("Add a short feedback note so the agents know what to change.");
      return;
    }
    setReviewBusy(true);
    setError("");
    try {
      await api.reviewStrategy(projectId, { decision, feedback: feedback.trim() || undefined });
      setFeedback("");
      window.setTimeout(load, 800);
    } catch (err) {
      setError(err.message);
    } finally {
      setReviewBusy(false);
    }
  };

  if (!run) {
    return (
      <section className="page-section">
        <div className="container">
          <div className="empty-state"><div className="spinner" /><p>Loading workspace…</p></div>
          {error && <div className="alert alert-error">{error}</div>}
        </div>
      </section>
    );
  }

  const outputs = run.outputs || {};
  const strategy = outputs.agent_social_media_strategy;
  const isRunning = ["running", "pending"].includes(run.workflow_status);
  const currentAgents = Array.isArray(run.current_agents) ? run.current_agents : [];
  const activeAgentLabels = currentAgents.map((agent) => AGENT_LABELS[agent] || agent);
  const steps = [
    { label: "Startup analysis", agents: ["startup_analysis"], done: Boolean(outputs.agent_startup_analysis) },
    { label: "Market research", agents: ["market_research"], done: Boolean(outputs.agent_market_research) },
    { label: "Customer research", agents: ["customer_research"], done: Boolean(outputs.agent_customer_research) },
    { label: "Strategy", agents: ["social_media_strategy", "strategy_optimization"], done: Boolean(strategy) },
    { label: "Founder review", agents: ["strategy_review"], done: Boolean(run.campaign_id) },
    { label: "Campaign", agents: ["campaign_orchestrator"], done: Boolean(run.campaign_id) },
  ].map((step) => ({
    ...step,
    active: isRunning && step.agents.some((agent) => currentAgents.includes(agent)),
  }));

  return (
    <section className="page-section">
      <div className="container">
        <div className="page-heading">
          <div>
            <span className="eyebrow">Project #{run.project_id}</span>
            <h1>Agent workspace</h1>
            <p>Research, strategy and approval in one place.</p>
          </div>
          <div className="heading-actions">
            <StatusPill value={run.workflow_status} />
            {run.campaign_id && (
              <Link to={`/campaigns/${run.campaign_id}`} className="btn btn-primary">
                Open campaign <ArrowIcon />
              </Link>
            )}
          </div>
        </div>

        {retrying && (
          <div className="alert alert-info">The previous run failed. Restarting the agents automatically…</div>
        )}
        {error && <div className="alert alert-error">{error}</div>}

        <div className="progress-card">
          <div className="progress-head">
            <strong>Workflow progress</strong>
            {isRunning && (
              <span className="live-label">
                <span className="pulse" />
                {activeAgentLabels.length ? `Working now: ${activeAgentLabels.join(", ")}` : "Agents starting"}
              </span>
            )}
          </div>
          <div className="progress-steps">
            {steps.map((step, index) => (
              <div
                className={`progress-step ${step.done ? "done" : ""} ${step.active ? "active" : ""}`}
                key={step.label}
              >
                <span>
                  {step.active ? <span className="mini-spinner" /> : step.done ? <CheckIcon /> : index + 1}
                </span>
                <p>{step.label}</p>
                {step.active && <small className="working-label">Working now</small>}
              </div>
            ))}
          </div>
        </div>

        <div className="report-grid">
          <article className="report-card">
            <div className="report-head"><span className="report-icon blue"><SparkIcon /></span><h2>Startup analysis</h2></div>
            <Markdown text={outputs.agent_startup_analysis} />
          </article>
          <article className="report-card">
            <div className="report-head"><span className="report-icon pink"><ChartIcon /></span><h2>Market research</h2></div>
            <Markdown text={outputs.agent_market_research} />
          </article>
          <article className="report-card">
            <div className="report-head"><span className="report-icon blue"><UsersIcon /></span><h2>Customer research</h2></div>
            <Markdown text={outputs.agent_customer_research} />
          </article>
        </div>

        <article className="strategy-card">
          <div className="strategy-card-head">
            <div>
              <span className="eyebrow">Social media strategy</span>
              <h2>Ready for your decision</h2>
            </div>
            <SparkIcon />
          </div>
          <StrategyView strategy={strategy} />
        </article>

        {run.workflow_status === "awaiting_review" && (
          <article className="review-card">
            <div className="review-card-head">
              <span className="review-icon"><ClockIcon /></span>
              <div>
                <h2>Founder review</h2>
                <p>Approve to start campaign orchestration, or explain what should change.</p>
              </div>
            </div>
            {outputs.strategy_feedback && (
              <div className="alert alert-info">Previous feedback: {outputs.strategy_feedback}</div>
            )}
            <textarea
              rows={4}
              value={feedback}
              onChange={(event) => setFeedback(event.target.value)}
              placeholder="Example: focus more on Instagram, reduce post frequency, and make the tone less formal."
            />
            <div className="review-actions">
              <button className="btn btn-primary" type="button" disabled={reviewBusy} onClick={() => submitReview("approve")}>
                Approve & build campaign <ArrowIcon />
              </button>
              <button className="btn btn-outline" type="button" disabled={reviewBusy} onClick={() => submitReview("revise")}>
                Request revision
              </button>
              <button className="btn btn-ghost" type="button" disabled={reviewBusy} onClick={() => submitReview("reject")}>
                Reject strategy
              </button>
            </div>
          </article>
        )}
      </div>
    </section>
  );
}

function UsersIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="9" cy="8" r="3.2" stroke="currentColor" strokeWidth="1.7" />
      <path d="M3.5 19c.4-3 2.4-4.6 5.5-4.6s5.1 1.6 5.5 4.6M16 6.5a3 3 0 0 1 0 5.8M17 14.8c2.2.4 3.4 1.8 3.6 4.2" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}
