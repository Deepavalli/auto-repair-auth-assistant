// Shared display helpers so every page labels decisions the same way.
export const DISPOSITION: Record<string, { label: string; chip: string }> = {
  approved: { label: "Approve", chip: "bg-emerald-500/15 text-emerald-400" },
  pended: { label: "Adjuster review", chip: "bg-amber-500/15 text-amber-400" },
  denied: { label: "Denied", chip: "bg-red-500/15 text-red-400" },
  "no-preapproval-required": { label: "No pre-approval needed", chip: "bg-sky-500/15 text-sky-400" },
};

export const dispositionOf = (d: string) =>
  DISPOSITION[d] ?? { label: d, chip: "bg-white/10 text-slate-300" };

export const statusChip = (s: string) =>
  s === "met" ? "bg-emerald-500/15 text-emerald-400"
  : s === "unmet" ? "bg-red-500/15 text-red-400"
  : "bg-amber-500/15 text-amber-400";

export const pct = (n: number | null | undefined) => (n == null ? "-" : `${Math.round(n * 100)}%`);

export const usd = (n: number | null | undefined) =>
  n == null ? "-" : n.toLocaleString("en-US", { style: "currency", currency: "USD" });

export const usDate = (iso: string) =>
  new Date(iso).toLocaleString("en-US", { month: "2-digit", day: "2-digit", year: "numeric", hour: "numeric", minute: "2-digit" });

export const field =
  "mt-1.5 w-full rounded-lg border border-white/10 bg-white/[0.03] px-3.5 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 outline-none focus:border-sky-500/50 focus:bg-white/[0.05]";
export const label = "text-xs font-medium uppercase tracking-wide text-slate-400";
export const primaryBtn =
  "rounded-lg bg-sky-500 px-6 py-2.5 text-sm font-semibold text-sky-950 transition hover:bg-sky-400 disabled:bg-slate-600 disabled:text-slate-400";
