import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { GITHUB_URL } from "../api";
import { useAuth } from "../auth";
import { GithubIcon, LogoMark } from "./Icons";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const scrollTo = (id) => {
    navigate("/");
    setOpen(false);
    window.setTimeout(() => {
      document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    }, 60);
  };

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <Link to={user ? "/dashboard" : "/"} className="brand">
          <LogoMark />
          <span>BrandPilot AI</span>
        </Link>

        <button
          className="menu-button"
          type="button"
          onClick={() => setOpen((value) => !value)}
          aria-label="Toggle navigation"
        >
          <span />
          <span />
          <span />
        </button>

        <nav className={`nav-links ${open ? "nav-open" : ""}`}>
          <button type="button" onClick={() => scrollTo("features")}>
            Features
          </button>
          <button type="button" onClick={() => scrollTo("workflow")}>
            How it works
          </button>
          <a href={GITHUB_URL} target="_blank" rel="noreferrer">
            <GithubIcon /> GitHub
          </a>
          {user ? (
            <>
              <Link to="/dashboard" onClick={() => setOpen(false)}>
                Dashboard
              </Link>
              <button
                type="button"
                className="btn btn-ghost btn-small"
                onClick={() => {
                  logout();
                  setOpen(false);
                  navigate("/");
                }}
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-ghost btn-small" onClick={() => setOpen(false)}>
                Log in
              </Link>
              <Link to="/signup" className="btn btn-primary btn-small" onClick={() => setOpen(false)}>
                Sign up free
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
