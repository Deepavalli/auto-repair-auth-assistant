import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Auto Repair Authorization Assistant",
  description: "Claude-powered agent that drafts auto insurance repair authorization requests",
};

const nav = [
  { href: "/", label: "Submit", icon: "＋" },
  { href: "/batch", label: "Batch", icon: "⚡" },
  { href: "/flow", label: "Agent flow", icon: "◈" },
  { href: "/requests", label: "Requests", icon: "▤" },
  { href: "/analytics", label: "Analytics", icon: "▧" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#0b1220] text-slate-100 antialiased">
        <div className="flex min-h-screen flex-col md:flex-row">
          <aside className="shrink-0 border-b border-white/5 bg-[#0d1526] px-5 py-5 md:flex md:w-64 md:flex-col md:border-b-0 md:border-r md:py-7">
            <div className="mb-4 md:mb-10">
              <div className="flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-500/15 text-sky-400">🚗</span>
                <span className="text-sm font-semibold tracking-tight">RepairAuth<span className="text-sky-400">AI</span></span>
              </div>
              <p className="mt-1 pl-10 text-[11px] text-slate-500">Auto claims agent · Claude</p>
            </div>
            <nav className="flex flex-wrap gap-1 md:flex-col">
              {nav.map((item) => (
                <Link key={item.href} href={item.href}
                  className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-400 transition hover:bg-white/5 hover:text-white">
                  <span className="text-xs opacity-70">{item.icon}</span>
                  {item.label}
                </Link>
              ))}
            </nav>
            <div className="mt-auto hidden rounded-xl border border-white/5 bg-white/[0.02] p-3 md:block">
              <p className="text-[11px] leading-relaxed text-slate-500">Synthetic data only. No real policyholder information.</p>
            </div>
          </aside>
          <main className="flex-1">
            <div className="mx-auto max-w-4xl px-4 py-8 md:px-10 md:py-10">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}
