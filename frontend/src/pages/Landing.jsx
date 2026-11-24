import { Link } from "react-router-dom";

import { GITHUB_URL } from "../api";
import {
  ArrowIcon,
  ChartIcon,
  CheckIcon,
  GithubIcon,
  GridIcon,
  ShieldIcon,
  SparkIcon,
} from "../components/Icons";

const features = [
  {
    icon: <ChartIcon />,
    title: "Three research agents",
    text: "Startup analysis, market research and customer research run together so your strategy is built on context, not guesses.",
  },
  {
    icon: <ShieldIcon />,
    title: "You stay in control",
    text: "Every strategy is paused for founder review. Approve, revise or reject before anything moves into execution.",
  },
  {
    icon: <GridIcon />,
    title: "Asset-aware planning",
    text: "The campaign calendar lists the exact images each post needs, then matches your uploads with AI suggestions.",
  },
  {
    icon: <SparkIcon />,
    title: "Publishing-ready drafts",
    text: "Captions, hashtags, CTAs and publishing jobs are prepared only after you approve the final posts.",
  },
];

const steps = [
  {
    number: "01",
    title: "Tell us about the startup",
    text: "Add your product, audience, goals, platforms and brand assets. Every field explains why it matters.",
  },
  {
    number: "02",
    title: "Agents analyze the market",
    text: "Watch startup, customer and market reports generate live in one clean workspace.",
  },
  {
    number: "03",
    title: "Approve the strategy",
    text: "Review the full social media strategy and send precise feedback before execution begins.",
  },
  {
    number: "04",
    title: "Launch the campaign",
    text: "Confirm assets, review ready posts and create publishing jobs without leaving the app.",
  },
];

export default function Landing() {
  return (
    <>
      <section className="hero">
        <div className="hero-glow" />
        <div className="container hero-grid">
          <div className="hero-copy">
            <span className="eyebrow">
              <SparkIcon /> AI marketing co-pilot for startups
            </span>
            <h1>
              From strategy to published campaigns, <em>without the guesswork.</em>
            </h1>
            <p className="hero-lead">
              BrandPilot AI researches your startup, builds a social media strategy, keeps you in the loop,
              then turns approval into a publishing-ready campaign calendar.
            </p>
            <div className="hero-actions">
              <Link to="/signup" className="btn btn-primary btn-large">
                Start free <ArrowIcon />
              </Link>
              <Link to="/login" className="btn btn-outline btn-large">
                Log in
              </Link>
              <a href={GITHUB_URL} target="_blank" rel="noreferrer" className="btn btn-ghost btn-large">
                <GithubIcon /> View project
              </a>
            </div>
            <div className="hero-proof">
              <span><CheckIcon /> Research-backed</span>
              <span><CheckIcon /> Human-approved</span>
              <span><CheckIcon /> Campaign-ready</span>
            </div>
          </div>

          <div className="hero-visual">
            <div className="mock-window">
              <div className="mock-topbar">
                <span />
                <span />
                <span />
                <strong>BrandPilot Workspace</strong>
              </div>
              <div className="mock-body">
                <div className="mock-heading">
                  <div>
                    <small>Today</small>
                    <h3>Your marketing command center</h3>
                  </div>
                  <span className="mock-badge">Agents live</span>
                </div>
                <div className="mock-agent-grid">
                  <div className="mock-card">
                    <span className="mock-icon blue">SA</span>
                    <div><strong>Startup analysis</strong><p>Complete</p></div>
                  </div>
                  <div className="mock-card">
                    <span className="mock-icon pink">MR</span>
                    <div><strong>Market research</strong><p>Complete</p></div>
                  </div>
                  <div className="mock-card">
                    <span className="mock-icon blue">CR</span>
                    <div><strong>Customer research</strong><p>Complete</p></div>
                  </div>
                </div>
                <div className="mock-review">
                  <div className="mock-review-head">
                    <strong>Strategy review</strong>
                    <span className="mock-badge pink">Waiting for you</span>
                  </div>
                  <p>LinkedIn · Education pillar · 8 posts · 2 weeks</p>
                  <div className="mock-buttons">
                    <span>Approve</span>
                    <span>Revise</span>
                  </div>
                </div>
                <div className="mock-timeline">
                  <div><span>01</span><p>Product intro</p></div>
                  <div><span>02</span><p>Customer story</p></div>
                  <div><span>03</span><p>Founder note</p></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="section section-white">
        <div className="container">
          <div className="section-heading">
            <span className="eyebrow">Built for the full journey</span>
            <h2>Everything your marketing needs, in one flow.</h2>
            <p>No scattered tools. No unexplained AI. Just a clear path from research to launch.</p>
          </div>
          <div className="feature-grid">
            {features.map((feature) => (
              <article className="feature-card" key={feature.title}>
                <span className="feature-icon">{feature.icon}</span>
                <h3>{feature.title}</h3>
                <p>{feature.text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="workflow" className="section section-soft">
        <div className="container">
          <div className="section-heading">
            <span className="eyebrow">How it works</span>
            <h2>Four steps from idea to execution.</h2>
          </div>
          <div className="step-grid">
            {steps.map((step) => (
              <article className="step-card" key={step.number}>
                <span className="step-number">{step.number}</span>
                <h3>{step.title}</h3>
                <p>{step.text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="cta-band">
        <div className="container cta-inner">
          <div>
            <span className="eyebrow light">Ready when you are</span>
            <h2>Give your startup a marketing co-pilot.</h2>
            <p>Create your first strategy run in a few minutes.</p>
          </div>
          <Link to="/signup" className="btn btn-pink btn-large">
            Create your workspace <ArrowIcon />
          </Link>
        </div>
      </section>
    </>
  );
}
