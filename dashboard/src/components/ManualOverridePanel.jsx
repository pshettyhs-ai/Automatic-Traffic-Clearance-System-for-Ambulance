import React, { useState } from "react";
import { api } from "../services/api.js";

/**
 * Manual override control. Requires the operator to log in (issues a JWT,
 * see backend/api/routes/auth.js) before force_red / clear_emergency can
 * be sent — matches the audit_trail requirement described in
 * diagrams/Database_Design.md.
 */
export default function ManualOverridePanel() {
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [statusMessage, setStatusMessage] = useState(null);
  const [busy, setBusy] = useState(false);

  async function handleLogin(e) {
    e.preventDefault();
    setBusy(true);
    setStatusMessage(null);
    try {
      const { token: newToken } = await api.login(username, password);
      setToken(newToken);
      setStatusMessage({ type: "success", text: "Logged in." });
    } catch (err) {
      setStatusMessage({ type: "error", text: err.message });
    } finally {
      setBusy(false);
    }
  }

  async function handleOverride(action) {
    if (!token) return;
    setBusy(true);
    setStatusMessage(null);
    try {
      await api.sendOverride(token, action);
      setStatusMessage({ type: "success", text: `Sent: ${action}` });
    } catch (err) {
      setStatusMessage({ type: "error", text: err.message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-4">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
        Manual Override
      </h2>

      {!token ? (
        <form onSubmit={handleLogin} className="flex flex-col gap-2">
          <input
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
            placeholder="Operator username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
          />
          <input
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
          <button
            type="submit"
            disabled={busy || !username || !password}
            className="rounded-md bg-sky-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
      ) : (
        <div className="flex flex-col gap-2">
          <button
            disabled={busy}
            onClick={() => handleOverride("force_red")}
            className="rounded-md bg-rose-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            Force all-red (maintenance)
          </button>
          <button
            disabled={busy}
            onClick={() => handleOverride("clear_emergency")}
            className="rounded-md bg-slate-700 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            Clear active emergency
          </button>
        </div>
      )}

      {statusMessage && (
        <p
          className={`mt-3 text-xs ${
            statusMessage.type === "error" ? "text-rose-400" : "text-emerald-400"
          }`}
        >
          {statusMessage.text}
        </p>
      )}

      <p className="mt-3 text-[11px] text-slate-600">
        Every override is written to <code>audit_trail</code> with the operator&apos;s user id —
        see <code>backend/api/routes/override.js</code>.
      </p>
    </div>
  );
}
