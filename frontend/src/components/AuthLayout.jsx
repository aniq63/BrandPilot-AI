import { Link } from "react-router-dom";

import { GITHUB_URL } from "../api";
import { CheckIcon, GithubIcon, ShieldIcon, SparkIcon } from "./Icons";

export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <section className="auth-page">
      <div className="container auth-grid">
        <div className="auth-card">
          <span className="eyebrow">Welcome to BrandPilot AI</span>
          <h1>{title}</h1>
          <p className="auth-subtitle">{subtitle}</p>
          {children}
          <div className="auth-footer">{footer}</div>
        </div>

        <aside className="auth-aside">
          <div className="auth-aside-top">
            <span className="aside-icon"><SparkIcon /></span>
            <h2>Your strategy workspace, built around you.</h2>
            <p>We collect only the context the agents need to produce useful marketing work.</p>
          </div>
          <ul className="aside-list">
            <li><CheckIcon /> Every form field explains why it is needed</li>
            <li><CheckIcon /> Your strategy pauses for your approval</li>
            <li><CheckIcon /> Nothing publishes before you approve the post</li>
          </ul>
          <div className="aside-trust">
            <ShieldIcon />
            <span>Private by design. Your workspace is tied to your account.</span>
          </div>
          <a className="aside-github" href={GITHUB_URL} target="_blank" rel="noreferrer">
            <GithubIcon /> Explore the open project on GitHub
          </a>
          <Link to="/" className="aside-back">
            Back to home
          </Link>
        </aside>
      </div>
    </section>
  );
}
