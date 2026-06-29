import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";

const STATUS_STYLES = {
  connected: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  connecting: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  disconnected: "bg-rose-500/15 text-rose-400 border-rose-500/30",
};

function Card({ label, value, sub, accent }) {
  return (
    <div className="flex-1 min-w-[180px] rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-1 text-2xl font-semibold ${accent || "text-slate-100"}`}>{value}</p>
      {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
    </div>
  );
}

function useClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}

export default function StatusCards() {
  const socketStatus = useSelector((s) => s.traffic.socketStatus);
  const emergencyActive = useSelector((s) => s.traffic.emergencyActive);
  const activeEmergencyLane = useSelector((s) => s.traffic.activeEmergencyLane);
  const eventsToday = useSelector((s) => s.traffic.emergencyEvents.length);
  const now = useClock();

  return (
    <div className="flex flex-wrap gap-4">
      <Card
        label="Connection"
        value={socketStatus}
        sub="Live WebSocket link to backend"
        accent={STATUS_STYLES[socketStatus]?.split(" ")[1]}
      />
      <Card
        label="Emergency Status"
        value={emergencyActive ? "ACTIVE" : "Clear"}
        sub={emergencyActive ? `Lane ${activeEmergencyLane} has priority` : "Normal cycling"}
        accent={emergencyActive ? "text-rose-400" : "text-emerald-400"}
      />
      <Card label="Events Logged" value={eventsToday} sub="In current session window" />
      <Card label="Last Update" value={now.toLocaleTimeString()} sub="Local clock, ticks every second" />
    </div>
  );
}
