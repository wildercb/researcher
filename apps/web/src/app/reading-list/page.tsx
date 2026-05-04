"use client";

import { useState, useEffect } from "react";
import { BookOpen, ExternalLink, Loader2 } from "lucide-react";
import Link from "next/link";
import { fetchItems, type ItemData } from "@/lib/api";

export default function ReadingListPage() {
  const [items, setItems] = useState<ItemData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const result = await fetchItems({ sort: "relevance", limit: 50 });
        setItems(result.items.filter(i => i.summary));
      } catch {
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <header className="border-b border-[var(--sidebar-border)] pb-4 mb-6">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <BookOpen size={20} className="text-[var(--accent)]" />
          Reading List
        </h2>
        <p className="text-xs text-[var(--muted)] mt-1">
          Top papers with summaries from your research feed
        </p>
      </header>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 size={24} className="animate-spin text-[var(--accent)]" />
        </div>
      )}

      {!loading && items.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20">
          <BookOpen size={48} className="text-[var(--muted)] mb-4" />
          <h3 className="text-lg font-medium mb-1">No enriched items yet</h3>
          <p className="text-sm text-[var(--muted)]">
            Items with summaries will appear here. Ask Claude Code to enrich items.
          </p>
        </div>
      )}

      {!loading && items.length > 0 && (
        <div className="space-y-3">
          {items.map((item) => (
            <Link
              key={item.id}
              href={`/item/${item.id}`}
              className="block rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-5 transition-colors hover:border-[var(--accent)]/30"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium flex items-center gap-1.5">
                    {item.title}
                    {item.url && <ExternalLink size={12} className="flex-shrink-0 opacity-30" />}
                  </div>
                  <div className="flex items-center gap-2 mt-1.5">
                    {item.authors.length > 0 && (
                      <span className="text-xs text-[var(--muted)]">
                        {item.authors.slice(0, 3).join(", ")}
                      </span>
                    )}
                    {item.venue && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--accent)]/15 text-[var(--accent)]">
                        {item.venue}
                      </span>
                    )}
                    {item.relevance_score !== null && (
                      <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                        item.relevance_score > 0.7
                          ? "bg-green-900/60 text-green-300"
                          : item.relevance_score >= 0.4
                          ? "bg-yellow-900/60 text-yellow-300"
                          : "bg-gray-800 text-gray-400"
                      }`}>
                        {(item.relevance_score * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  {item.summary && (
                    <p className="text-xs text-[var(--muted)] mt-2 leading-relaxed">
                      {item.summary}
                    </p>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
