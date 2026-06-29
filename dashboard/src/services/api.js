const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:4000";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  getRecentEvents: (hours = 24, limit = 100) => request(`/api/events?hours=${hours}&limit=${limit}`),

  getEvent: (id) => request(`/api/events/${id}`),

  getLaneCycles: (hours = 6) => request(`/api/lanes/cycles?hours=${hours}`),

  getNodeHealth: () => request("/api/lanes/health"),

  login: (username, password) =>
    request("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),

  sendOverride: (token, action, lane) =>
    request("/api/override", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ action, lane }),
    }),
};

export { API_BASE_URL };
