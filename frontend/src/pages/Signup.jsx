import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth";
import AuthLayout from "../components/AuthLayout";
import Field from "../components/Field";

export default function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", email: "", password: "" });
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
      await signup(form);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthLayout
      title="Create your workspace"
      subtitle="Start building strategies and campaigns that are actually ready to launch."
      footer={
        <>
          Already have an account? <Link to="/login">Log in</Link>
        </>
      }
    >
      <form className="form-stack" onSubmit={submit}>
        <Field
          label="Your name"
          hint="Shown in your workspace and used to personalize your dashboard."
          required
        >
          <input
            type="text"
            value={form.username}
            onChange={(event) => update("username", event.target.value)}
            placeholder="e.g. Ayesha Khan"
            minLength={1}
            maxLength={100}
            required
          />
        </Field>

        <Field
          label="Work email"
          hint="Used for login and to keep your projects tied to your account."
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
          hint="At least 8 characters. Stored as a secure hash, never as plain text."
          required
        >
          <input
            type="password"
            value={form.password}
            onChange={(event) => update("password", event.target.value)}
            placeholder="Create a strong password"
            minLength={8}
            required
          />
        </Field>

        {error && <div className="alert alert-error">{error}</div>}

        <button className="btn btn-primary btn-full" type="submit" disabled={busy}>
          {busy ? "Creating workspace…" : "Create account"}
        </button>
      </form>
    </AuthLayout>
  );
}
