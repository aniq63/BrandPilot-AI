import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api";
import Field from "../components/Field";
import { ArrowIcon, UploadIcon } from "../components/Icons";

const GOAL_OPTIONS = [
  "Brand awareness",
  "Lead generation",
  "Customer acquisition",
  "Product launch",
  "Community growth",
  "Sales conversions",
  "Retention",
];

const PLATFORM_OPTIONS = ["LinkedIn", "Instagram", "X / Twitter", "Facebook", "TikTok", "YouTube", "Other"];

const splitList = (value) =>
  String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

export default function NewProject() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    startup_name: "",
    website_url: "",
    product_name: "",
    product_description: "",
    industry: "",
    product_pricing: "",
    main_competitors: "",
    ideal_customers: "",
    target_market: "",
    customer_pain_points: "",
    existing_customer_base: "",
    brand_tone: "Confident and practical",
    brand_identity: "",
    campaign_duration: "4 weeks",
    goals: [],
    accounts: [{
      platform: "LinkedIn",
      username: "",
      profile_url: "",
      account_type: "Company",
      connected_account_id: "",
      platform_account_id: "",
      connection_status: "pending",
      publishing_enabled: true,
      publishing_scopes: "publish_content",
      token_expires_at: "",
    }],
    brand_logo: null,
    brand_images: [],
    customGoal: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const update = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const toggleGoal = (goal) => {
    setForm((current) => ({
      ...current,
      goals: current.goals.includes(goal)
        ? current.goals.filter((item) => item !== goal)
        : [...current.goals, goal],
    }));
  };

  const addCustomGoal = () => {
    const goal = form.customGoal.trim();
    if (!goal) return;
    if (!form.goals.includes(goal)) {
      update("goals", [...form.goals, goal]);
    }
    update("customGoal", "");
  };

  const updateAccount = (index, key, value) => {
    const accounts = form.accounts.map((account, position) =>
      position === index ? { ...account, [key]: value } : account,
    );
    update("accounts", accounts);
  };

  const submit = async (event) => {
    event.preventDefault();
    setError("");

    if (!form.goals.length) {
      setError("Choose at least one marketing goal.");
      return;
    }

    const publishingAccount = form.accounts.find((account) => {
      if (!account.profile_url || !account.publishing_enabled) return false;
      return (
        !account.connected_account_id ||
        !account.platform_account_id ||
        account.connection_status !== "connected" ||
        !splitList(account.publishing_scopes).length
      );
    });
    if (publishingAccount) {
      setError(
        `Add a secure connection ID, platform account ID, connected status, and publishing scopes for ${publishingAccount.platform || "each publishing account"}.`
      );
      return;
    }

    setBusy(true);
    try {
      let brandMedia = { brand_logo: null, brand_assets: [] };
      if (form.brand_logo || form.brand_images.length) {
        const data = new FormData();
        if (form.brand_logo) data.append("brand_logo", form.brand_logo);
        form.brand_images.forEach((file) => data.append("brand_images", file));
        brandMedia = await api.uploadBrandMedia(data);
      }

      const payload = {
        startup_name: form.startup_name,
        website_url: form.website_url,
        product_name: form.product_name,
        product_description: form.product_description,
        industry: form.industry,
        product_pricing: form.product_pricing || undefined,
        main_competitors: splitList(form.main_competitors),
        ideal_customers: form.ideal_customers || undefined,
        target_market: form.target_market || undefined,
        customer_pain_points: splitList(form.customer_pain_points),
        existing_customer_base: form.existing_customer_base || undefined,
        brand_tone: form.brand_tone || undefined,
        brand_identity: form.brand_identity || undefined,
        campaign_duration: form.campaign_duration || undefined,
        marketing_goals: form.goals,
        social_media_accounts: form.accounts
          .filter((account) => account.platform && account.profile_url)
          .map((account) => ({
            platform: account.platform,
            username: account.username || "Brand account",
            profile_url: account.profile_url,
            account_type: account.account_type || undefined,
            connected_account_id: account.connected_account_id || undefined,
            platform_account_id: account.platform_account_id || undefined,
            connection_status: account.connection_status || "pending",
            publishing_enabled: Boolean(account.publishing_enabled),
            publishing_scopes: splitList(account.publishing_scopes),
            token_expires_at: account.token_expires_at
              ? new Date(account.token_expires_at).toISOString()
              : undefined,
          })),
        brand_logo: brandMedia.brand_logo || undefined,
        brand_assets: brandMedia.brand_assets.length ? brandMedia.brand_assets : undefined,
      };

      const result = await api.submitRun(payload);
      navigate(`/runs/${result.project_id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="page-section">
      <div className="container narrow-container">
        <div className="page-heading">
          <div>
            <span className="eyebrow">New strategy run</span>
            <h1>Tell us about your startup.</h1>
            <p>Each field has a short explanation so you know exactly why the agents need it.</p>
          </div>
        </div>

        <form className="form-card" onSubmit={submit}>
          <fieldset className="form-section">
            <legend><span>01</span> Startup information</legend>
            <p className="section-note">This becomes the foundation for every agent report.</p>
            <div className="field-grid">
              <Field label="Startup name" required hint="Used in reports and campaign naming.">
                <input value={form.startup_name} onChange={(e) => update("startup_name", e.target.value)} placeholder="BrandPilot" required />
              </Field>
              <Field label="Website URL" required hint="The agent reads your site to ground analysis in real content.">
                <input type="url" value={form.website_url} onChange={(e) => update("website_url", e.target.value)} placeholder="https://yourstartup.com" required />
              </Field>
              <Field label="Product name" required hint="Helps research agents find relevant market and customer signals.">
                <input value={form.product_name} onChange={(e) => update("product_name", e.target.value)} placeholder="Your product" required />
              </Field>
              <Field label="Industry" required hint="Used to focus market research and competitor discovery.">
                <input value={form.industry} onChange={(e) => update("industry", e.target.value)} placeholder="SaaS, healthcare, fintech…" required />
              </Field>
              <Field label="Product description" wide required hint="Explain what it does and the problem it solves. This shapes the whole strategy.">
                <textarea rows={4} value={form.product_description} onChange={(e) => update("product_description", e.target.value)} placeholder="Describe your product in 2–4 sentences." required />
              </Field>
              <Field label="Pricing" hint="Optional. Helps the strategy avoid claims that conflict with your model.">
                <input value={form.product_pricing} onChange={(e) => update("product_pricing", e.target.value)} placeholder="Free tier + $29/month" />
              </Field>
              <Field label="Main competitors" hint="Optional. Comma-separated. Research will compare against these names.">
                <input value={form.main_competitors} onChange={(e) => update("main_competitors", e.target.value)} placeholder="Competitor A, Competitor B" />
              </Field>
            </div>
          </fieldset>

          <fieldset className="form-section">
            <legend><span>02</span> Target audience</legend>
            <p className="section-note">Customer research uses this to build sharper personas and messaging.</p>
            <div className="field-grid">
              <Field label="Ideal customers" hint="Who should see these campaigns? Be specific about roles or situations.">
                <input value={form.ideal_customers} onChange={(e) => update("ideal_customers", e.target.value)} placeholder="Early-stage founders and marketing leads" />
              </Field>
              <Field label="Target market" hint="Geography or market segment, so research stays relevant.">
                <input value={form.target_market} onChange={(e) => update("target_market", e.target.value)} placeholder="US and UK startups" />
              </Field>
              <Field label="Customer pain points" wide hint="Comma-separated. These become the core messaging angles.">
                <input value={form.customer_pain_points} onChange={(e) => update("customer_pain_points", e.target.value)} placeholder="Manual reporting, slow launches, unclear ownership" />
              </Field>
              <Field label="Existing customer base" hint="Optional. Helps calibrate tone and growth goals.">
                <input value={form.existing_customer_base} onChange={(e) => update("existing_customer_base", e.target.value)} placeholder="120 active users, mostly solo founders" />
              </Field>
            </div>
          </fieldset>

          <fieldset className="form-section">
            <legend><span>03</span> Marketing goals</legend>
            <p className="section-note">Pick the outcomes the strategy should optimize for.</p>
            <div className="goal-chips">
              {GOAL_OPTIONS.map((goal) => (
                <button
                  type="button"
                  key={goal}
                  className={`goal-chip ${form.goals.includes(goal) ? "selected" : ""}`}
                  onClick={() => toggleGoal(goal)}
                >
                  {goal}
                </button>
              ))}
            </div>
            <div className="custom-goal">
              <input
                value={form.customGoal}
                onChange={(e) => update("customGoal", e.target.value)}
                placeholder="Add a custom goal"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addCustomGoal();
                  }
                }}
              />
              <button type="button" className="btn btn-ghost btn-small" onClick={addCustomGoal}>Add goal</button>
            </div>
            {form.goals.length > 0 && (
              <p className="selected-note">Selected: {form.goals.join(" · ")}</p>
            )}
          </fieldset>

          <fieldset className="form-section">
            <legend><span>04</span> Brand & resources</legend>
            <p className="section-note">This keeps generated content on-brand and limits platforms to what you actually use.</p>
            <div className="field-grid">
              <Field label="Brand tone" hint="Guides captions and calls to action.">
                <select value={form.brand_tone} onChange={(e) => update("brand_tone", e.target.value)}>
                  <option>Confident and practical</option>
                  <option>Friendly and conversational</option>
                  <option>Bold and energetic</option>
                  <option>Calm and authoritative</option>
                  <option>Playful and creative</option>
                </select>
              </Field>
              <Field label="Campaign duration" hint="Used to build a realistic posting calendar.">
                <select value={form.campaign_duration} onChange={(e) => update("campaign_duration", e.target.value)}>
                  <option>1 week</option>
                  <option>2 weeks</option>
                  <option>4 weeks</option>
                  <option>6 weeks</option>
                  <option>8 weeks</option>
                </select>
              </Field>
              <Field label="Brand identity" wide hint="Optional. Colors, visual style or positioning the agents should respect.">
                <textarea rows={3} value={form.brand_identity} onChange={(e) => update("brand_identity", e.target.value)} placeholder="Clean product shots, sky blue accents, founder-led voice." />
              </Field>
            </div>

            <div className="account-builder">
              <div className="account-builder-head">
                <div>
                  <strong>Publishing-ready social accounts</strong>
                  <p>Add the profile URL and secure publishing details. Agents need these to create publishable jobs for approved posts.</p>
                </div>
                <button
                  type="button"
                  className="btn btn-ghost btn-small"
                  onClick={() => update("accounts", [...form.accounts, {
                    platform: "",
                    username: "",
                    profile_url: "",
                    account_type: "",
                    connected_account_id: "",
                    platform_account_id: "",
                    connection_status: "pending",
                    publishing_enabled: true,
                    publishing_scopes: "publish_content",
                    token_expires_at: "",
                  }])}
                >
                  + Add account
                </button>
              </div>
              <details className="account-help" open>
                <summary>How to fill these fields</summary>
                <div className="account-help-body">
                  <p><strong>Example Instagram account</strong></p>
                  <ul>
                    <li><strong>Platform:</strong> choose <code>Instagram</code>.</li>
                    <li><strong>Username / page name:</strong> use your public handle or page name, for example <code>BrandPilot Official</code>.</li>
                    <li><strong>Profile URL:</strong> paste the full public profile link, for example <code>https://www.instagram.com/brandpilot/</code>.</li>
                    <li><strong>Allow publishing jobs:</strong> keep checked only when the agent should create publishing jobs for approved posts.</li>
                    <li><strong>Secure connection ID:</strong> use the ID of your OAuth connection record, for example <code>ig_conn_brandpilot_001</code>. Never paste an access token here.</li>
                    <li><strong>Page / channel ID:</strong> use the Instagram Business/Creator account ID or connected Facebook Page ID from Meta Graph API, for example <code>17841400000000000</code>.</li>
                    <li><strong>Connection status:</strong> choose <code>Connected</code> only after authorization is complete. If it is pending or disconnected, uncheck “Allow publishing jobs”.</li>
                    <li><strong>Scopes:</strong> enter <code>publish_content</code>. Add your real provider scopes later, such as <code>instagram_content_publish,pages_manage_posts</code>.</li>
                    <li><strong>Expiry:</strong> enter the credential expiry date if you know it, otherwise leave it blank.</li>
                  </ul>
                  <p className="account-help-note">This app currently creates publishing-ready jobs after post approval. It does not call Instagram’s publish API yet.</p>
                </div>
              </details>
              {form.accounts.map((account, index) => (
                <div className="account-entry" key={index}>
                  <div className="account-row">
                    <select value={account.platform} onChange={(e) => updateAccount(index, "platform", e.target.value)}>
                      {PLATFORM_OPTIONS.map((option) => <option key={option}>{option}</option>)}
                      {!PLATFORM_OPTIONS.includes(account.platform) && <option>{account.platform}</option>}
                    </select>
                    <input value={account.username} onChange={(e) => updateAccount(index, "username", e.target.value)} placeholder="BrandPilot Official" />
                    <input value={account.profile_url} onChange={(e) => updateAccount(index, "profile_url", e.target.value)} placeholder="https://www.instagram.com/brandpilot/" />
                    <button
                      type="button"
                      className="icon-button"
                      aria-label="Remove account"
                      onClick={() => update("accounts", form.accounts.filter((_, position) => position !== index))}
                    >
                      ×
                    </button>
                  </div>
                  <div className="account-publishing">
                    <label className="publishing-toggle">
                      <input
                        type="checkbox"
                        checked={Boolean(account.publishing_enabled)}
                        onChange={(e) => updateAccount(index, "publishing_enabled", e.target.checked)}
                      />
                      Allow the agent to create publishing jobs for this account
                    </label>
                    <div className="publishing-grid">
                      <input
                        value={account.connected_account_id}
                        onChange={(e) => updateAccount(index, "connected_account_id", e.target.value)}
                        placeholder="ig_conn_brandpilot_001"
                        aria-label="Secure connection ID"
                      />
                      <input
                        value={account.platform_account_id}
                        onChange={(e) => updateAccount(index, "platform_account_id", e.target.value)}
                        placeholder="17841400000000000"
                        aria-label="Page or channel ID"
                      />
                      <select
                        value={account.connection_status}
                        onChange={(e) => updateAccount(index, "connection_status", e.target.value)}
                        aria-label="Connection status"
                      >
                        <option value="pending">Connection pending</option>
                        <option value="connected">Connected</option>
                        <option value="disconnected">Disconnected</option>
                      </select>
                      <input
                        value={account.publishing_scopes}
                        onChange={(e) => updateAccount(index, "publishing_scopes", e.target.value)}
                        placeholder="Scopes: publish_content"
                        aria-label="Publishing scopes"
                      />
                      <input
                        type="datetime-local"
                        value={account.token_expires_at}
                        onChange={(e) => updateAccount(index, "token_expires_at", e.target.value)}
                        aria-label="Credential expiry"
                      />
                    </div>
                    <p>
                      Use a secure connection reference from your social integration, not a raw access token. Publishing jobs are only created after you approve each post.
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div className="upload-block">
              <div className="upload-copy">
                <span className="upload-icon"><UploadIcon /></span>
                <div>
                  <strong>Brand assets</strong>
                  <p>Optional now. Upload a logo and product images so campaign asset suggestions are stronger later.</p>
                </div>
              </div>
              <div className="field-grid">
                <Field label="Brand logo" hint="Single image. Used as a reference asset by the vision agent.">
                  <input type="file" accept="image/*" onChange={(e) => update("brand_logo", e.target.files?.[0] || null)} />
                </Field>
                <Field label="Brand images" hint="Multiple images allowed. JPG, PNG, WEBP or GIF up to 10 MB each.">
                  <input type="file" accept="image/*" multiple onChange={(e) => update("brand_images", Array.from(e.target.files || []))} />
                </Field>
              </div>
            </div>
          </fieldset>

          {error && <div className="alert alert-error">{error}</div>}

          <div className="form-actions">
            <button className="btn btn-primary btn-large" type="submit" disabled={busy}>
              {busy ? "Starting agents…" : "Start agent analysis"} <ArrowIcon />
            </button>
            <p>Your strategy will pause for your review before any campaign is created.</p>
          </div>
        </form>
      </div>
    </section>
  );
}
