import React from "react";
import { useSelector } from "react-redux";

const LANE_LABELS = { 1: "North", 2: "East", 3: "South", 4: "West" };

function activeBulb(phase) {
  if (phase === "GREEN") return "green";
  if (phase === "YELLOW") return "yellow";
  return "red"; // RED, ALL_RED_CLEARANCE, UNKNOWN all read as the safe default: red lit
}

function SignalHead({ lane, phase, updatedAt }) {
  const active = activeBulb(phase);
  return (
    <div className="flex flex-col items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <p className="text-sm font-semibold text-slate-200">{LANE_LABELS[lane] || `Lane ${lane}`}</p>
      <div className="flex flex-col gap-1.5 rounded-lg bg-slate-950 p-2">
        {["red", "yellow", "green"].map((color) => (
          <span
            key={color}
            className={`h-6 w-6 rounded-full ${
              active === color
                ? color === "red"
                  ? "bg-signal-red shadow-[0_0_12px_2px_rgba(220,38,38,0.7)]"
                  : color === "yellow"
                  ? "bg-signal-yellow shadow-[0_0_12px_2px_rgba(202,138,4,0.7)]"
                  : "bg-signal-green shadow-[0_0_12px_2px_rgba(22,163,74,0.7)]"
                : "bg-slate-800"
            }`}
          />
        ))}
      </div>
      <p className="text-xs font-mono text-slate-400">{phase}</p>
      <p className="text-[10px] text-slate-600">
        {updatedAt ? new Date(updatedAt).toLocaleTimeString() : "no data yet"}
      </p>
    </div>
  );
}

export default function LaneSignalBoard() {
  const lanes = useSelector((s) => s.traffic.lanes);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-4">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
        Intersection Signal Status
      </h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {Object.values(lanes).map((l) => (
          <SignalHead key={l.lane} lane={l.lane} phase={l.phase} updatedAt={l.updatedAt} />
        ))}
      </div>
    </div>
  );
}
