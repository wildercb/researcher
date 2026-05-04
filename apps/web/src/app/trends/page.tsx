"use client";

import { useState, useEffect } from "react";
import { TrendingUp, Loader2 } from "lucide-react";
import { fetchTrends, type TrendData } from "@/lib/api";

export default function TrendsPage() {
  const [trends, setTrends] = useState<TrendData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const result = await fetchTrends();
        // Sort by velocity descending
        const sorted = [...result.trends].sort((a, b) => b.velocity - a.velocity);
        setTrends(sorted);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch trends");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const maxVelocity = trends.length > 0 ? Math.max(...trends.map((t) => t.velocity)) : 1;

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

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 size={24} className="animate-spin text-[var(--accent)]" />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-800/50 bg-red-900/20 p-4 mb-6">
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && trends.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20">
          <TrendingUp size={48} className="text-[var(--muted)] mb-4" />
          <h3 className="text-lg font-medium mb-1">No trends yet</h3>
          <p className="text-sm text-[var(--muted)]">
            Trends will appear here once the pipeline has processed enough items.
          </p>
        </div>
      )}

      {/* Trend Cards */}
      {!loading && trends.length > 0 && (
        <div className="space-y-3">
          {trends.map((trend) => (
            <div
              key={trend.topic}
              className="rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-5"
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium">{trend.topic}</h3>
                <div className="flex items-center gap-3 text-xs text-[var(--muted)]">
                  <span>
                    Total: <span className="text-[var(--foreground)] font-medium">{trend.count}</span>
                  </span>
                  <span>
                    7d: <span className="text-[var(--foreground)] font-medium">{trend.recent_count}</span>
                  </span>
                </div>
              </div>

              {/* Velocity Bar */}
              <div className="flex items-center gap-3">
                <div className="flex-1 h-2 rounded-full bg-[var(--input-bg)] overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${maxVelocity > 0 ? (trend.velocity / maxVelocity) * 100 : 0}%`,
                      background:
                        trend.velocity / maxVelocity > 0.6
                          ? "var(--accent)"
                          : trend.velocity / maxVelocity > 0.3
                          ? "#eab308"
                          : "#71717a",
                    }}
                  />
                </div>
                <span className="text-xs text-[var(--muted)] w-16 text-right">
                  v={trend.velocity.toFixed(2)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
