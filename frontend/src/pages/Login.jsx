import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../auth";
import AuthLayout from "../components/AuthLayout";
import Field from "../components/Field";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const update = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(form);
      navigate(location.state?.from || "/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Log in to continue your strategy review and campaign work."
      footer={
        <>
          New to BrandPilot AI? <Link to="/signup">Create an account</Link>
        </>
      }
    >
      <form className="form-stack" onSubmit={submit}>
        <Field
          label="Work email"
          hint="Use the email address you registered with."
          required
        >
          <input
            type="email"
            value={form.email}
            onChange={(event) => update("email", event.target.value)}
            placeholder="you@company.com"
            required
          />
        </Field>

        <Field
          label="Password"
          hint="Your account password. We never display or store it in the browser."
          required
        >
          <input
            type="password"
            value={form.password}
            onChange={(event) => update("password", event.target.value)}
            placeholder="Enter your password"
            required
          />
        </Field>

        {error && <div className="alert alert-error">{error}</div>}

        <button className="btn btn-primary btn-full" type="submit" disabled={busy}>
          {busy ? "Logging in…" : "Log in"}
        </button>
      </form>
    </AuthLayout>
  );
}
