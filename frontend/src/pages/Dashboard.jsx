import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api";
import { useAuth } from "../auth";
import { ArrowIcon, ChartIcon, ClockIcon, GridIcon, SparkIcon } from "../components/Icons";
import StatusPill from "../components/StatusPill";

export default function Dashboard() {
  const { user } = useAuth();
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const summaries = await api.listRuns();
      const detailed = await Promise.all(
        summaries.map(async (run) => {
          try {
            const detail = await api.getRun(run.project_id);
            return { ...run, campaign_id: detail.campaign_id };
          } catch {
            return run;
          }
        }),
      );
      setRuns(detailed);
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 6000);
    return () => window.clearInterval(timer);
  }, [load]);

  const awaiting = runs.filter((run) => run.workflow_status === "awaiting_review").length;
  const campaigns = runs.filter((run) => run.campaign_id).length;

  return (
    <section className="page-section">
      <div className="container">
        <div className="page-heading dashboard-heading">
          <div>
            <span className="eyebrow">Your workspace</span>
            <h1>Welcome back, {user?.username || "founder"}.</h1>
            <p>Every strategy, review and campaign in one place.</p>
          </div>
          <Link to="/projects/new" className="btn btn-primary">
            New strategy run <ArrowIcon />
          </Link>
        </div>

        <div className="stat-grid">
          <div className="stat-card">
            <span className="stat-icon blue"><GridIcon /></span>
            <div><strong>{runs.length}</strong><p>Total projects</p></div>
          </div>
          <div className="stat-card">
            <span className="stat-icon pink"><ClockIcon /></span>
            <div><strong>{awaiting}</strong><p>Awaiting your review</p></div>
          </div>
          <div className="stat-card">
            <span className="stat-icon blue"><ChartIcon /></span>
            <div><strong>{campaigns}</strong><p>Campaigns created</p></div>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {loading ? (
          <div className="empty-state"><div className="spinner" /><p>Loading your projects…</p></div>
        ) : runs.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon"><SparkIcon /></span>
            <h2>No strategy runs yet</h2>
            <p>Add your startup context and let the agents build your first marketing strategy.</p>
            <Link to="/projects/new" className="btn btn-primary">Start your first run <ArrowIcon /></Link>
          </div>
        ) : (
          <div className="run-grid">
            {runs.map((run) => (
              <article className="run-card" key={run.project_id}>
                <div className="run-card-top">
                  <span className="run-id">Project #{run.project_id}</span>
                  <StatusPill value={run.workflow_status} />
                </div>
                <h3>{run.startup_name}</h3>
                <p className="run-thread">Thread {run.thread_id?.slice(0, 8) || "pending"}</p>
                <div className="run-card-actions">
                  <Link to={`/runs/${run.project_id}`} className="btn btn-outline btn-small">
                    Open workspace <ArrowIcon />
                  </Link>
                  {run.campaign_id && (
                    <Link to={`/campaigns/${run.campaign_id}`} className="btn btn-ghost btn-small">
                      Campaign #{run.campaign_id}
                    </Link>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
