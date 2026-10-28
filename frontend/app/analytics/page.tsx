"use client";

import { useEffect, useState } from "react";
import { getAnalytics, Analytics } from "@/lib/api";
import { dispositionOf, pct, usd } from "@/lib/ui";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis } from "recharts";

const COLORS: Record<string, string> = {
  approved: "#10b981",
  pended: "#f59e0b",
  denied: "#ef4444",
  "no-preapproval-required": "#0ea5e9",
};
const tooltipStyle = { background: "#0d1526", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#e2e8f0" };

export default function AnalyticsPage() {
  const [data, setData] = useState<Analytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { getAnalytics().then(setData).catch((e) => setError(String(e))); }, []);

  if (error) return <p className="text-red-400">{error}</p>;
  if (!data) return <p className="text-slate-400">Loading...</p>;

  const pieData = Object.entries(data.by_disposition).map(([k, v]) => ({ key: k, name: dispositionOf(k).label, value: v }));
  const barData = Object.entries(data.by_service).map(([name, count]) => ({ name, count }));

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Analytics</h1>
      <p className="mt-2 text-sm text-slate-400">Aggregate view across all processed repair requests.</p>

      <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat label="Total requests" value={data.total_requests} />
        <Stat label="Need pre-approval" value={data.preapproval_required} />
        <Stat label="Avg confidence" value={pct(data.avg_confidence)} />
        <Stat label="Total estimates" value={usd(data.total_estimated_cost)} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Panel title="Recommendation breakdown">
          <PieChart>
            <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={100} paddingAngle={3}>
              {pieData.map((p) => <Cell key={p.key} fill={COLORS[p.key] ?? "#64748b"} stroke="none" />)}
            </Pie>
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ color: "#94a3b8", fontSize: 13 }} />
          </PieChart>
        </Panel>
        <Panel title="Requests by repair type">
          <BarChart data={barData} layout="vertical" margin={{ left: 20 }}>
            <XAxis type="number" allowDecimals={false} stroke="#64748b" fontSize={12} />
            <YAxis type="category" dataKey="name" width={150} stroke="#64748b" fontSize={12} />
            <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
            <Bar dataKey="count" fill="#0ea5e9" radius={[0, 4, 4, 0]} />
          </BarChart>
        </Panel>
      </div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactElement }) {
  return (
    <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
      <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400">{title}</p>
      <div className="mt-4 h-72"><ResponsiveContainer width="100%" height="100%">{children}</ResponsiveContainer></div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5">
      <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight">{value}</p>
    </div>
  );
}
