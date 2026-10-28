"use client";

import { useEffect, useState } from "react";
import { listRequests, overrideRequest, acordUrl, getHealth, RepairAuthResult } from "@/lib/api";
import { dispositionOf, statusChip, pct, usd, usDate, primaryBtn } from "@/lib/ui";

export default function RequestsPage() {
  const [requests, setRequests] = useState<RepairAuthResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const [keyRequired, setKeyRequired] = useState(false);

  useEffect(() => {
    listRequests().then(setRequests).catch((e) => setError(String(e))).finally(() => setLoading(false));
    getHealth().then((h) => setKeyRequired(h.reviewer_key_required)).catch(() => {});
  }, []);

  function onOverridden(updated: RepairAuthResult) {
    setRequests((rs) => rs.map((r) => (r.id === updated.id ? updated : r)));
  }

  if (loading) return <p className="text-slate-400">Loading...</p>;

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Processed requests</h1>
      <p className="mt-2 text-sm text-slate-400">Every repair authorization the agent has reviewed. A claims reviewer can override any recommendation.</p>
      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}

      {requests.length === 0 ? (
        <p className="mt-8 text-slate-500">Nothing submitted yet.</p>
      ) : (
        <div className="mt-8 space-y-2">
          {requests.map((r) => {
            const d = dispositionOf(r.disposition);
            return (
              <div key={r.id} className="overflow-hidden rounded-xl border border-white/5 bg-white/[0.02]">
                <button onClick={() => setOpenId(openId === r.id ? null : r.id)}
                  className="flex w-full flex-wrap items-center justify-between gap-3 px-5 py-4 text-left hover:bg-white/[0.02]">
                  <div>
                    <p className="font-medium text-slate-200">{r.policyholder_name} <span className="text-sm text-slate-500">· {r.claim_number}</span></p>
                    <p className="text-sm text-slate-500">{r.service_name} · {usd(r.estimated_cost)} · {usDate(r.created_at)}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    {r.overridden && <span className="rounded-full bg-violet-500/15 px-2.5 py-0.5 text-xs font-semibold text-violet-400">overridden</span>}
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${d.chip}`}>{d.label}</span>
                    <span className="text-sm text-slate-400">{pct(r.confidence)}</span>
                  </div>
                </button>
                {openId === r.id && <Detail request={r} onDone={onOverridden} keyRequired={keyRequired} />}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Detail({ request, onDone, keyRequired }: { request: RepairAuthResult; onDone: (r: RepairAuthResult) => void; keyRequired: boolean }) {
  const [decision, setDecision] = useState<"APPROVED" | "DENIED">("APPROVED");
  const [reason, setReason] = useState("");
  const [reviewer, setReviewer] = useState("");
  const [reviewerKey, setReviewerKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [overrideError, setOverrideError] = useState<string | null>(null);

  async function submit() {
    setSaving(true); setOverrideError(null);
    try { onDone(await overrideRequest(request.id, decision, reason, reviewer, reviewerKey)); }
    catch (e) { setOverrideError(e instanceof Error ? e.message : "Override failed"); }
    finally { setSaving(false); }
  }

  const input = "w-full rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 outline-none focus:border-sky-500/50";

  return (
    <div className="space-y-4 border-t border-white/5 px-5 py-4 text-sm">
      {request.criteria.map((c, i) => (
        <div key={i} className="flex items-start justify-between gap-3">
          <div><p className="text-slate-200">{c.criterion}</p><p className="text-slate-500">{c.justification}</p></div>
          <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold ${statusChip(c.status)}`}>{c.status}</span>
        </div>
      ))}
      {request.draft && <p className="whitespace-pre-wrap rounded-lg bg-white/[0.02] p-3 text-slate-300">{request.draft}</p>}
      <a href={acordUrl(request.id)} target="_blank" rel="noreferrer" className="inline-block text-sky-400 hover:underline">View ACORD-style JSON ↗</a>

      <div className="space-y-3 border-t border-white/5 pt-4">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Reviewer override</p>
        {request.overridden && (
          <p className="text-violet-400">Overridden to <strong>{request.override_decision}</strong> by {request.override_by}: {request.override_reason}</p>
        )}
        <div className="flex gap-2">
          {(["APPROVED", "DENIED"] as const).map((d) => (
            <button key={d} onClick={() => setDecision(d)}
              className={`rounded-lg px-3 py-1.5 font-semibold ${decision === d ? (d === "APPROVED" ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400") : "bg-white/[0.03] text-slate-400"}`}>
              {d}
            </button>
          ))}
        </div>
        <input value={reviewer} onChange={(e) => setReviewer(e.target.value)} placeholder="Reviewer name" className={input} />
        <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Reason for override" className={input} />
        {keyRequired && (
          <input type="password" value={reviewerKey} onChange={(e) => setReviewerKey(e.target.value)} placeholder="Reviewer key" className={input} />
        )}
        {overrideError && <p className="text-red-400">{overrideError}</p>}
        <button onClick={submit} disabled={saving || !reviewer || !reason || (keyRequired && !reviewerKey)} className={primaryBtn}>{saving ? "Saving..." : "Submit override"}</button>
      </div>
    </div>
  );
}
