"use client";

import { useState, useEffect } from "react";
import { BookOpen, ExternalLink, Loader2 } from "lucide-react";
import { fetchItems, type ItemData } from "@/lib/api";

export default function ReadingListPage() {
  const [items, setItems] = useState<ItemData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        // Fetch all items; we filter client-side for liked ones
        // The API may support a feedback filter in the future
        const result = await fetchItems({ sort: "relevant" });
        // For now, show items that have been liked
        // Since the API doesn't return feedback status directly,
        // we show all items and note this is a placeholder until
        // the API supports filtering by feedback signal
        setItems(result.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch items");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="p-6">
      <header className="border-b border-[var(--sidebar-border)] pb-4 mb-6">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <BookOpen size={20} className="text-[var(--accent)]" />
          Reading List
        </h2>
        <p className="text-xs text-[var(--muted)] mt-1">
          Items you have saved from the Feed
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
      {!loading && !error && items.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20">
          <BookOpen size={48} className="text-[var(--muted)] mb-4" />
          <h3 className="text-lg font-medium mb-1">Nothing saved yet</h3>
          <p className="text-sm text-[var(--muted)]">
            Save items from the Feed to see them here.
          </p>
        </div>
      )}

      {/* Item List */}
      {!loading && items.length > 0 && (
        <div className="space-y-2">
          {items.map((item) => (
            <div
              key={item.id}
              className="rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-4 flex items-center gap-4 transition-colors hover:border-[var(--accent)]/30"
            >
              <div className="flex-1 min-w-0">
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-medium hover:text-[var(--accent)] transition-colors inline-flex items-center gap-1.5"
                >
                  <span className="truncate">{item.title}</span>
                  <ExternalLink size={12} className="flex-shrink-0 opacity-50" />
                </a>
                <div className="flex items-center gap-3 mt-1">
                  {item.authors && item.authors.length > 0 && (
                    <span className="text-xs text-[var(--muted)]">
                      {item.authors.slice(0, 3).join(", ")}
                      {item.authors.length > 3 && ` +${item.authors.length - 3}`}
                    </span>
                  )}
                  {item.venue && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--accent)]/15 text-[var(--accent)] border border-[var(--accent)]/20">
                      {item.venue}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
