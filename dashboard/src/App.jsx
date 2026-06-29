import React, { useEffect } from "react";
import { useDispatch } from "react-redux";

import { initSocket } from "./services/socket.js";
import StatusCards from "./components/StatusCards.jsx";
import LaneSignalBoard from "./components/LaneSignalBoard.jsx";
import EmergencyTimeline from "./components/EmergencyTimeline.jsx";
import AnalyticsCharts from "./components/AnalyticsCharts.jsx";
import ManualOverridePanel from "./components/ManualOverridePanel.jsx";

export default function App() {
  const dispatch = useDispatch();

  useEffect(() => {
    const socket = initSocket(dispatch);
    return () => {
      socket.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-6 sm:px-8">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">
            Traffic Clearance System <span className="text-slate-500">— Operator Dashboard</span>
          </h1>
          <p className="text-sm text-slate-500">
            Junction 01 · Raspberry Pi 4B (detection) + Pico WH (control)
          </p>
        </div>
      </header>

      <main className="flex flex-col gap-6">
        <StatusCards />
        <LaneSignalBoard />

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <EmergencyTimeline />
          </div>
          <ManualOverridePanel />
        </div>

        <AnalyticsCharts />
      </main>

      <footer className="mt-10 text-center text-xs text-slate-600">
        Traffic Clearance System for Emergency Vehicles — built by Pavan Shetty H S and team
      </footer>
    </div>
  );
}
