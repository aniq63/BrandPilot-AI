import { Link } from "react-router-dom";

import { GITHUB_URL } from "../api";
import { LogoMark } from "./Icons";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <LogoMark size={30} />
          <div>
            <strong>BrandPilot AI</strong>
            <p>Strategy to launch, with you in control.</p>
          </div>
        </div>
        <div className="footer-links">
          <Link to="/">Home</Link>
          <Link to="/dashboard">Dashboard</Link>
          <a href={GITHUB_URL} target="_blank" rel="noreferrer">
            GitHub
          </a>
        </div>
        <span className="footer-note">Built for founders who move fast.</span>
      </div>
    </footer>
  );
}
