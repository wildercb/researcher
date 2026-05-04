import { BarChart3 } from "lucide-react";

const metrics = [
  { label: "Relevance", value: "--", description: "How relevant are retrieved items" },
  { label: "Freshness", value: "--", description: "How recent are the sources" },
  { label: "Coverage", value: "--", description: "Breadth across seed topics" },
  { label: "Accuracy", value: "--", description: "Factual accuracy of summaries" },
];

export default function EvalPage() {
  return (
    <div className="p-6">
      <header className="border-b border-[var(--sidebar-border)] pb-4 mb-6">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <BarChart3 size={20} className="text-[var(--accent)]" />
          Eval Dashboard
        </h2>
        <p className="text-xs text-[var(--muted)] mt-1">
          Monitor system quality scores and pipeline health
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((m) => (
          <div
            key={m.label}
            className="rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-6"
          >
            <p className="text-xs text-[var(--muted)] mb-1">{m.label}</p>
            <p className="text-3xl font-bold text-[var(--accent)]">{m.value}</p>
            <p className="text-xs text-[var(--muted)] mt-2">{m.description}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-6 min-h-[300px] flex items-center justify-center">
        <p className="text-sm text-[var(--muted)]">
          Eval score history and charts will appear here once the pipeline is running.
        </p>
      </div>
    </div>
  );
}
