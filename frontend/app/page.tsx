"use client";

import { useEffect, useState } from "react";
import { submitRequest, draftAppeal, listGuidelines, Guideline, RepairAuthResult } from "@/lib/api";
import { dispositionOf, statusChip, pct, usd, field, label, primaryBtn } from "@/lib/ui";

const SAMPLE = {
  policyholder_name: "Maria Lopez",
  carrier_name: "Lakeshore Mutual Auto",
  vehicle: "2022 Honda CR-V",
  service_code: "AUTO-GLS-RPL",
  service_name: "Windshield replacement",
  estimated_cost: "1180",
  note_text:
    "Insured reports a rock strike on I-90 on 10/12/2026. Inspection found a 14-inch crack across the driver's critical viewing area; too long for resin chip repair. Four photos attached. Comprehensive coverage with $250 deductible confirmed active.",
};

type Form = typeof SAMPLE;

export default function SubmitPage() {
  const [form, setForm] = useState<Form>(SAMPLE);
  const [guidelines, setGuidelines] = useState<Guideline[]>([]);
  const [result, setResult] = useState<RepairAuthResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [appeal, setAppeal] = useState<string | null>(null);
  const [appealing, setAppealing] = useState(false);

  useEffect(() => { listGuidelines().then(setGuidelines).catch(() => {}); }, []);

  const update = (k: keyof Form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm({ ...form, [k]: e.target.value });

  function pickService(e: React.ChangeEvent<HTMLSelectElement>) {
    const g = guidelines.find((x) => x.service_code === e.target.value);
    setForm({ ...form, service_code: e.target.value, service_name: g?.service_name ?? form.service_name });
  }

  async function onSubmit() {
    setLoading(true); setError(null); setResult(null); setAppeal(null);
    try {
      setResult(await submitRequest({
        ...form,
        estimated_cost: form.estimated_cost ? Number(form.estimated_cost) : null,
      }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  async function onAppeal() {
    if (!result) return;
    setAppealing(true); setAppeal(null);
    try {
      setAppeal((await draftAppeal(result.id)).appeal);
    } catch (e) {
      setAppeal(e instanceof Error ? e.message : "Appeal failed");
    } finally {
      setAppealing(false);
    }
  }

  const d = result ? dispositionOf(result.disposition) : null;

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Submit a repair authorization</h1>
      <p className="mt-2 text-sm text-slate-400">
        Enter the claim details and the estimator&apos;s note. Claude checks the carrier guideline and drafts a justified authorization request.
      </p>

      <div className="mt-8 space-y-5 rounded-2xl border border-white/5 bg-white/[0.02] p-6">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <div><span className={label}>Policyholder</span><input className={field} value={form.policyholder_name} onChange={update("policyholder_name")} /></div>
          <div><span className={label}>Carrier</span><input className={field} value={form.carrier_name} onChange={update("carrier_name")} /></div>
          <div><span className={label}>Vehicle</span><input className={field} value={form.vehicle} onChange={update("vehicle")} placeholder="2022 Honda CR-V" /></div>
          <div><span className={label}>Estimated cost (USD)</span><input className={field} type="number" value={form.estimated_cost} onChange={update("estimated_cost")} /></div>
          <div>
            <span className={label}>Repair operation</span>
            {guidelines.length > 0 ? (
              <select className={field} value={form.service_code} onChange={pickService}>
                {guidelines.map((g) => <option key={g.guideline_id} value={g.service_code}>{g.service_code} · {g.service_name}</option>)}
              </select>
            ) : (
              <input className={field} value={form.service_code} onChange={update("service_code")} />
            )}
          </div>
          <div><span className={label}>Repair description</span><input className={field} value={form.service_name} onChange={update("service_name")} /></div>
        </div>
        <div><span className={label}>Estimator / adjuster note</span><textarea className={field} rows={5} value={form.note_text} onChange={update("note_text")} /></div>
        <button onClick={onSubmit} disabled={loading} className={primaryBtn}>{loading ? "Claude is reviewing..." : "Run agent"}</button>
      </div>

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}

      {result && d && (
        <div className="mt-6 overflow-hidden rounded-2xl border border-white/5 bg-white/[0.02]">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/5 px-6 py-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-400">Recommendation · {result.claim_number}</p>
              <span className={`mt-1 inline-block rounded-full px-3 py-1 text-sm font-semibold ${d.chip}`}>{d.label}</span>
            </div>
            <div className="flex gap-6 text-right">
              <div><p className="text-xs uppercase tracking-wide text-slate-400">Estimate</p><p className="text-lg font-semibold">{usd(result.estimated_cost)}</p></div>
              {result.confidence !== null && (
                <div><p className="text-xs uppercase tracking-wide text-slate-400">Confidence</p><p className="text-lg font-semibold">{pct(result.confidence)}</p></div>
              )}
            </div>
          </div>

          <div className="space-y-5 p-6">
            {result.guideline_id && <p className="text-sm text-slate-400">Guideline <span className="font-mono text-slate-200">{result.guideline_id}</span></p>}

            {result.criteria.map((c, i) => (
              <div key={i} className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
                <div className="flex items-start justify-between gap-3">
                  <span className="text-sm font-medium text-slate-200">{c.criterion}</span>
                  <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold ${statusChip(c.status)}`}>{c.status}</span>
                </div>
                <p className="mt-1.5 text-sm text-slate-400">{c.justification}</p>
              </div>
            ))}

            {result.draft && (
              <div>
                <p className={label}>Drafted authorization request</p>
                <p className="mt-2 whitespace-pre-wrap rounded-xl border border-white/5 bg-white/[0.02] p-4 text-sm leading-relaxed text-slate-300">{result.draft}</p>
              </div>
            )}

            {result.criteria.some((c) => c.status !== "met") && (
              <div className="border-t border-white/5 pt-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className={label}>Likely to be pended or denied</p>
                    <p className="mt-1 text-sm text-slate-400">Some criteria are unmet or uncertain. Draft a reconsideration request.</p>
                  </div>
                  <button onClick={onAppeal} disabled={appealing}
                    className="shrink-0 rounded-lg border border-sky-500/40 px-4 py-2 text-sm font-semibold text-sky-400 transition hover:bg-sky-500/10 disabled:opacity-50">
                    {appealing ? "Drafting..." : "Draft reconsideration"}
                  </button>
                </div>
                {appeal && <p className="mt-4 whitespace-pre-wrap rounded-xl border border-white/5 bg-white/[0.02] p-4 text-sm leading-relaxed text-slate-300">{appeal}</p>}
              </div>
            )}

            <details className="text-sm text-slate-400">
              <summary className="cursor-pointer">Agent trace</summary>
              <ol className="mt-2 list-decimal space-y-1 pl-5 font-mono text-xs">{result.trace.map((t, i) => <li key={i}>{t}</li>)}</ol>
            </details>
          </div>
        </div>
      )}
    </div>
  );
}
