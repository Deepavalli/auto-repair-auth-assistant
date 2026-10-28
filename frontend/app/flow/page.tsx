"use client";

import { useState } from "react";
import ReactFlow, { Background, Controls, Node, Edge, MarkerType } from "reactflow";
import "reactflow/dist/style.css";
import { submitRequest } from "@/lib/api";
import { primaryBtn } from "@/lib/ui";

const SAMPLE = {
  policyholder_name: "Maria Lopez",
  carrier_name: "Lakeshore Mutual Auto",
  vehicle: "2022 Honda CR-V",
  service_code: "AUTO-GLS-RPL",
  service_name: "Windshield replacement",
  estimated_cost: 1180,
  note_text: "Rock strike on 10/12/2026. 14-inch crack across the driver's view, too long for chip repair. Photos attached. Comprehensive coverage active.",
};

const NODES = [
  { id: "extract", label: "Extract", desc: "Read claim, identify repair code" },
  { id: "triage", label: "Triage", desc: "Is pre-approval required?" },
  { id: "retrieve", label: "Retrieve", desc: "Find carrier guideline" },
  { id: "evaluate", label: "Evaluate (Claude)", desc: "Check each criterion" },
  { id: "draft", label: "Draft (Claude)", desc: "Write authorization request" },
];

export default function FlowPage() {
  const [visited, setVisited] = useState<Set<string>>(new Set());
  const [running, setRunning] = useState(false);
  const [trace, setTrace] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setRunning(true); setVisited(new Set()); setTrace([]); setError(null);
    try {
      const result = await submitRequest(SAMPLE, false); // dry run: not saved to history
      // Light up only the nodes that actually fired, in order.
      for (const line of result.trace) {
        const n = NODES.find((x) => line.startsWith(x.id));
        if (n) {
          setVisited((prev) => new Set(prev).add(n.id));
          await new Promise((r) => setTimeout(r, 350));
        }
      }
      setTrace(result.trace);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Run failed");
    } finally {
      setRunning(false);
    }
  }

  const nodes: Node[] = NODES.map((n, i) => {
    const active = visited.has(n.id);
    return {
      id: n.id,
      position: { x: 100, y: i * 110 },
      data: { label: (
        <div className="text-left">
          <div className="text-sm font-semibold">{n.label}</div>
          <div className="text-[11px] opacity-70">{n.desc}</div>
        </div>
      ) },
      style: {
        width: 230, borderRadius: 12, padding: 12,
        border: active ? "1px solid #0ea5e9" : "1px solid rgba(255,255,255,0.1)",
        background: active ? "rgba(14,165,233,0.12)" : "rgba(255,255,255,0.02)",
        color: active ? "#7dd3fc" : "#94a3b8",
      },
    };
  });

  const edges: Edge[] = NODES.slice(0, -1).map((n, i) => ({
    id: `${n.id}-${NODES[i + 1].id}`,
    source: n.id,
    target: NODES[i + 1].id,
    animated: running,
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { stroke: "rgba(255,255,255,0.15)" },
  }));

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Agent flow</h1>
      <p className="mt-2 text-sm text-slate-400">
        The five-node LangGraph pipeline. Run it to see which nodes fire; for repairs that need no pre-approval, retrieval and Claude steps stay dim. Demo runs are not saved to request history.
      </p>
      <button onClick={run} disabled={running} className={`mt-6 ${primaryBtn}`}>{running ? "Running..." : "Run pipeline"}</button>
      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
      <div className="mt-6 h-[620px] rounded-2xl border border-white/5 bg-white/[0.02]">
        <ReactFlow nodes={nodes} edges={edges} fitView proOptions={{ hideAttribution: true }}>
          <Background color="#1e293b" gap={20} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
      {trace.length > 0 && (
        <ol className="mt-4 list-decimal space-y-1 pl-5 font-mono text-xs text-slate-400">{trace.map((t, i) => <li key={i}>{t}</li>)}</ol>
      )}
    </div>
  );
}
