const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const TOKEN_KEY = "brandpilot_token";
const USER_KEY = "brandpilot_user";

export const GITHUB_URL = "https://github.com/aniq63/BrandPilot-AI";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || "null");
  } catch {
    return null;
  }
}

export function setSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

function errorText(detail) {
  if (!detail) return "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || String(item)).join(", ");
  }
  return "Something went wrong. Please try again.";
}

async function request(path, options = {}) {
  const { method = "GET", body, auth = true, form = false } = options;
  const headers = {};

  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  if (body !== undefined && !form) {
    headers["Content-Type"] = "application/json";
  }

  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body:
        body === undefined
          ? undefined
          : form
            ? body
            : JSON.stringify(body),
    });
  } catch {
    throw new Error("Cannot reach BrandPilot AI. Start the backend server first.");
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    throw new Error(errorText(data?.detail));
  }

  return data;
}

export const api = {
  signup: (payload) =>
    request("/auth/signup", { method: "POST", body: payload, auth: false }),
  login: (payload) =>
    request("/auth/login", { method: "POST", body: payload, auth: false }),
  me: () => request("/auth/me"),

  listRuns: () => request("/agents/runs"),
  submitRun: (payload) => request("/agents/runs", { method: "POST", body: payload }),
  getRun: (projectId) => request(`/agents/runs/${projectId}`),
  retryRun: (projectId) =>
    request(`/agents/runs/${projectId}/retry`, { method: "POST" }),
  reviewStrategy: (projectId, payload) =>
    request(`/agents/runs/${projectId}/review`, { method: "POST", body: payload }),

  uploadBrandMedia: (formData) =>
    request("/uploads/brand", { method: "POST", body: formData, form: true }),

  getCampaign: (campaignId) => request(`/campaigns/${campaignId}`),
  uploadCampaignAssets: (campaignId, formData) =>
    request(`/campaigns/${campaignId}/assets`, {
      method: "POST",
      body: formData,
      form: true,
    }),
  requestAssetSuggestions: (campaignId) =>
    request(`/campaigns/${campaignId}/asset-suggestions`, { method: "POST" }),
  getAssetSuggestions: (campaignId) =>
    request(`/campaigns/${campaignId}/asset-suggestions`),
  regenerateAssetSuggestions: (campaignId) =>
    request(`/campaigns/${campaignId}/asset-suggestions/regenerate`, {
      method: "POST",
    }),
  confirmAssignments: (campaignId, payload) =>
    request(`/campaigns/${campaignId}/asset-assignments/confirm`, {
      method: "POST",
      body: payload,
    }),
  addManualAssignment: (campaignId, payload) =>
    request(`/campaigns/${campaignId}/asset-assignments`, {
      method: "POST",
      body: payload,
    }),
  prepareContent: (campaignId) =>
    request(`/campaigns/${campaignId}/prepare-content`, { method: "POST" }),
  regenerateContent: (campaignId) =>
    request(`/campaigns/${campaignId}/prepare-content/regenerate`, {
      method: "POST",
    }),
  listPosts: (campaignId) => request(`/campaigns/${campaignId}/posts`),
  reviewPreparedPost: (preparedPostId, payload) =>
    request(`/campaigns/posts/${preparedPostId}/review`, {
      method: "POST",
      body: payload,
    }),
  createPublishingJobs: (campaignId) =>
    request(`/campaigns/${campaignId}/publishing-jobs`, { method: "POST" }),
  listPublishingJobs: (campaignId) =>
    request(`/campaigns/${campaignId}/publishing-jobs`),
};
