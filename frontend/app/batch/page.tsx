"use client";

import { useState } from "react";
import { runBatch, BatchItemResult, SubmitRequest } from "@/lib/api";
import { dispositionOf, pct, usd, primaryBtn } from "@/lib/ui";

const CARRIER = "Lakeshore Mutual Auto";

// A sample queue: an approval, a likely pend, a no-pre-approval tow, and an ADAS calibration.
const QUEUE: SubmitRequest[] = [
  {
    policyholder_name: "Maria Lopez", carrier_name: CARRIER, vehicle: "2022 Honda CR-V",
    service_code: "AUTO-GLS-RPL", service_name: "Windshield replacement", estimated_cost: 1180,
    note_text: "Rock strike 10/12/2026. 14-inch crack across driver's view, too long for chip repair. Photos attached. Comprehensive active.",
  },
  {
    policyholder_name: "Daniel Brooks", carrier_name: CARRIER, vehicle: "2015 Ford Focus",
    service_code: "AUTO-STR-FRM", service_name: "Structural / frame repair", estimated_cost: 6900,
    note_text: "Front-end collision 10/3/2026. Left frame rail appears bent. Vehicle ACV $7,800. No frame measurement yet. Collision active.",
  },
  {
    policyholder_name: "Priya Shah", carrier_name: CARRIER, vehicle: "2019 Tesla Model 3",
    service_code: "AUTO-TOW-STD", service_name: "Standard tow to repair facility", estimated_cost: 145,
    note_text: "Not drivable after collision; towed 8 miles to network shop.",
  },
  {
    policyholder_name: "Kevin Nguyen", carrier_name: CARRIER, vehicle: "2023 Toyota RAV4",
    service_code: "AUTO-ADAS-CAL", service_name: "ADAS camera/sensor recalibration", estimated_cost: 395,
    note_text: "Lane-departure camera on windshield. Windshield replaced under approved glass claim. Static calibration per Toyota OEM procedure with pre/post scans.",
  },
];

export default function BatchPage() {
  const [results, setResults] = useState<BatchItemResult[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setRunning(true); setResults([]); setError(null);
    try { setResults(await runBatch(QUEUE)); }
    catch (e) { setError(e instanceof Error ? e.message : "Batch failed"); }
    finally { setRunning(false); }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Batch processing</h1>
      <p className="mt-2 text-sm text-slate-400">Run a queue of pending repair requests through the agent at once, e.g. a shop&apos;s end-of-day submissions.</p>
      <button onClick={run} disabled={running} className={`mt-6 ${primaryBtn}`}>
        {running ? `Processing ${QUEUE.length} requests...` : `Run batch (${QUEUE.length} requests)`}
      </button>
      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
      {results.length > 0 && (
        <>
          <p className="mt-6 text-sm text-slate-400">
            {results.filter((i) => i.ok).length} of {results.length} processed
            {results.some((i) => !i.ok) && <span className="text-red-400"> · {results.filter((i) => !i.ok).length} failed</span>}
          </p>
          <div className="mt-3 space-y-2">
            {results.map((item) => {
              if (!item.ok || !item.result) {
                return (
                  <div key={item.index} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-500/20 bg-red-500/[0.04] px-5 py-4">
                    <div>
                      <p className="font-medium text-slate-200">{item.policyholder_name}</p>
                      <p className="text-sm text-slate-500">{item.service_name}</p>
                    </div>
                    <p className="max-w-md text-right text-sm text-red-400">Failed: {item.error}</p>
                  </div>
                );
              }
              const r = item.result;
              const d = dispositionOf(r.disposition);
              return (
                <div key={item.index} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/5 bg-white/[0.02] px-5 py-4">
                  <div>
                    <p className="font-medium text-slate-200">{r.policyholder_name} · <span className="text-slate-400">{r.vehicle}</span></p>
                    <p className="text-sm text-slate-500">{r.service_name} · {usd(r.estimated_cost)}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${d.chip}`}>{d.label}</span>
                    <span className="text-sm text-slate-400">{pct(r.confidence)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
