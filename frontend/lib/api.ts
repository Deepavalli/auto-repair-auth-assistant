// All calls to the FastAPI backend live here. The base URL comes from an env
// var so the deployed UI can point at the deployed API without code changes.
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api";

export interface CriterionResult {
  criterion: string;
  status: "met" | "unmet" | "uncertain" | string;
  justification: string;
}

export interface RepairAuthResult {
  id: string;
  claim_number: string;
  policyholder_name: string;
  carrier_name: string | null;
  vehicle: string | null;
  service_code: string;
  service_name: string;
  estimated_cost: number | null;
  note_text: string;
  preapproval_required: boolean;
  guideline_id: string | null;
  criteria: CriterionResult[];
  draft: string | null;
  confidence: number | null;
  disposition: string;
  trace: string[];
  created_at: string;
  overridden: boolean;
  override_decision: string | null;
  override_reason: string | null;
  override_by: string | null;
}

export interface SubmitRequest {
  policyholder_name: string;
  service_code: string;
  service_name: string;
  note_text: string;
  carrier_name?: string;
  claim_number?: string;
  vehicle?: string;
  estimated_cost?: number | null;
}

export interface Guideline {
  guideline_id: string;
  carrier_name: string;
  service_code: string;
  service_name: string;
  preapproval_required: boolean;
  criteria: string[];
}

export interface BatchItemResult {
  index: number;
  policyholder_name: string;
  service_name: string;
  ok: boolean;
  result: RepairAuthResult | null;
  error: string | null;
}

export interface Analytics {
  total_requests: number;
  preapproval_required: number;
  preapproval_not_required: number;
  overridden: number;
  avg_confidence: number;
  total_estimated_cost: number;
  by_disposition: Record<string, number>;
  by_service: Record<string, number>;
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    let detail = "";
    try { detail = (await res.json()).detail ?? ""; } catch { /* non-JSON error body */ }
    throw new Error(`${path} failed: ${res.status}${detail ? ` - ${detail}` : ""}`);
  }
  return res.json();
}

// save=false runs the agent without storing the result (used by the Agent Flow demo).
export const submitRequest = (body: SubmitRequest, save = true) =>
  call<RepairAuthResult>(`/submit${save ? "" : "?save=false"}`, { method: "POST", body: JSON.stringify(body) });

export const runBatch = (reqs: SubmitRequest[]) =>
  call<BatchItemResult[]>("/batch", { method: "POST", body: JSON.stringify(reqs) });

export const listRequests = () => call<RepairAuthResult[]>("/requests");

export const listGuidelines = () => call<Guideline[]>("/guidelines");

export const getAnalytics = () => call<Analytics>("/analytics");

export const draftAppeal = (request_id: string) =>
  call<{ appeal: string }>("/appeal", { method: "POST", body: JSON.stringify({ request_id }) });

export const getHealth = () => call<{ status: string; reviewer_key_required: boolean }>("/health");

// reviewerKey is sent as X-Reviewer-Key; the API requires it only when REVIEWER_API_KEY is set.
export const overrideRequest = (
  request_id: string, decision: "APPROVED" | "DENIED", reason: string, reviewer: string, reviewerKey = "",
) =>
  call<RepairAuthResult>("/override", {
    method: "POST",
    headers: reviewerKey ? { "X-Reviewer-Key": reviewerKey } : {},
    body: JSON.stringify({ request_id, decision, reason, reviewer }),
  });

export const acordUrl = (id: string) => `${API_BASE}/requests/${id}/acord`;
