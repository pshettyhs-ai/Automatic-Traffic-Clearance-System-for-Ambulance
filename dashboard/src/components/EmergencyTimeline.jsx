import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { api } from "../services/api.js";

const LANE_LABELS = { 1: "North", 2: "East", 3: "South", 4: "West" };

export default function EmergencyTimeline() {
  const liveEvents = useSelector((s) => s.traffic.emergencyEvents);
  const [historicalEvents, setHistoricalEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getRecentEvents(24, 50)
      .then((data) => {
        if (!cancelled) setHistoricalEvents(data.events);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Merge live (just-arrived) events with the historical fetch, de-duplicated by id.
  const merged = [...liveEvents, ...historicalEvents].reduce((acc, ev) => {
    const key = ev.id ?? `${ev.lane}-${ev.detected_at}`;
    if (!acc.some((e) => (e.id ?? `${e.lane}-${e.detected_at}`) === key)) acc.push(ev);
    return acc;
  }, []);
  merged.sort((a, b) => (b.detected_at || 0) - (a.detected_at || 0));

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-4">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
        Emergency Event Timeline (24h)
      </h2>

      {loading && <p className="text-sm text-slate-500">Loading event history…</p>}
      {error && (
        <p className="text-sm text-rose-400">
          Couldn&apos;t load history from the API ({error}) — showing live events only.
        </p>
      )}

      {!loading && merged.length === 0 && (
        <p className="text-sm text-slate-500">No emergency events in the last 24 hours.</p>
      )}

      <ul className="divide-y divide-slate-800">
        {merged.slice(0, 20).map((ev) => (
          <li key={ev.id ?? `${ev.lane}-${ev.detected_at}`} className="flex items-center justify-between py-2.5">
            <div>
              <p className="text-sm font-medium text-slate-200">
                {LANE_LABELS[ev.lane] || `Lane ${ev.lane}`} lane
              </p>
              <p className="text-xs text-slate-500">
                {ev.detected_at ? new Date(ev.detected_at * 1000).toLocaleString() : "unknown time"}
              </p>
            </div>
            <span className="rounded-full bg-rose-500/15 px-2.5 py-1 text-xs font-mono text-rose-400">
              conf {Number(ev.confidence).toFixed(2)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
