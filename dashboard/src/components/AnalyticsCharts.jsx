import React, { useEffect, useMemo, useState } from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from "chart.js";
import { api } from "../services/api.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

function bucketEventsByHour(events) {
  const buckets = Array.from({ length: 24 }, (_, i) => ({ hour: i, count: 0 }));
  events.forEach((ev) => {
    if (!ev.detected_at) return;
    const hour = new Date(ev.detected_at * 1000).getHours();
    buckets[hour].count += 1;
  });
  return buckets;
}

export default function AnalyticsCharts() {
  const [events, setEvents] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getRecentEvents(24, 500)
      .then((data) => {
        if (!cancelled) setEvents(data.events);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const buckets = useMemo(() => bucketEventsByHour(events), [events]);

  const chartData = {
    labels: buckets.map((b) => `${b.hour}:00`),
    datasets: [
      {
        label: "Emergency triggers",
        data: buckets.map((b) => b.count),
        backgroundColor: "rgba(220, 38, 38, 0.6)",
        borderRadius: 4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { display: false },
    },
    scales: {
      x: { ticks: { color: "#94a3b8" }, grid: { color: "#1e293b" } },
      y: {
        ticks: { color: "#94a3b8", precision: 0 },
        grid: { color: "#1e293b" },
        beginAtZero: true,
      },
    },
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-4">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
        Emergency Triggers by Hour (24h)
      </h2>
      {error ? (
        <p className="text-sm text-rose-400">Couldn&apos;t load analytics data ({error}).</p>
      ) : (
        <Bar data={chartData} options={chartOptions} />
      )}
    </div>
  );
}
