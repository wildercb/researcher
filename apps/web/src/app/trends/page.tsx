import { TrendingUp } from "lucide-react";

export default function TrendsPage() {
  return (
    <div className="p-6">
      <header className="border-b border-[var(--sidebar-border)] pb-4 mb-6">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <TrendingUp size={20} className="text-[var(--accent)]" />
          Trends
        </h2>
        <p className="text-xs text-[var(--muted)] mt-1">
          Track emerging patterns across your research areas
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-3">
        {/* Placeholder cards */}
        {["Rising Topics", "Frequency Analysis", "Sentiment Shifts"].map(
          (title) => (
            <div
              key={title}
              className="rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-6 min-h-[200px] flex flex-col"
            >
              <h3 className="text-sm font-medium mb-2">{title}</h3>
              <div className="flex-1 flex items-center justify-center">
                <p className="text-xs text-[var(--muted)] text-center">
                  Trend visualization will appear here
                </p>
              </div>
            </div>
          )
        )}
      </div>
    </div>
  );
}
