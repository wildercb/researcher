"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  FileText,
  Search,
  ThumbsUp,
  EyeOff,
  Play,
  ExternalLink,
  Loader2,
} from "lucide-react";
import { fetchItems, sendFeedback, triggerPipeline, type ItemData } from "@/lib/api";

type SortMode = "recent" | "relevant";

export default function FeedPage() {
  const [items, setItems] = useState<ItemData[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchText, setSearchText] = useState("");
  const [sortMode, setSortMode] = useState<SortMode>("recent");
  const [sourceFilter, setSourceFilter] = useState("");
  const [sources, setSources] = useState<string[]>([]);
  const [pipelineStatus, setPipelineStatus] = useState<string | null>(null);
  const [feedbackIds, setFeedbackIds] = useState<Record<number, string>>({});
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadItems = useCallback(
    async (q?: string) => {
      setLoading(true);
      setError(null);
      try {
        const params: Record<string, string> = {};
        if (q) params.q = q;
        if (sortMode === "recent") params.sort = "recent";
        if (sortMode === "relevant") params.sort = "relevant";
        if (sourceFilter) params.source = sourceFilter;
        const result = await fetchItems(params);
        setItems(result.items);
        setTotal(result.total);

        // Extract unique sources for the filter dropdown
        const uniqueSources = Array.from(
          new Set(result.items.map((item) => item.source).filter(Boolean))
        );
        if (uniqueSources.length > 0) {
          setSources((prev) =>
            prev.length >= uniqueSources.length ? prev : uniqueSources
          );
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch items");
      } finally {
        setLoading(false);
      }
    },
    [sortMode, sourceFilter]
  );

  useEffect(() => {
    loadItems(searchText || undefined);
  }, [loadItems, searchText]);

  const handleSearchChange = (value: string) => {
    setSearchText(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      loadItems(value || undefined);
    }, 400);
  };

  const handleFeedback = async (itemId: number, signal: string) => {
    try {
      await sendFeedback(itemId, signal);
      setFeedbackIds((prev) => ({ ...prev, [itemId]: signal }));
      // If downvoted, visually fade it out after a moment
      if (signal === "hidden") {
        setTimeout(() => {
          setItems((prev) => prev.filter((i) => i.id !== itemId));
        }, 500);
      }
    } catch {}
  };

  const handleRunPipeline = async () => {
    setPipelineStatus("Fetching...");
    try {
      await triggerPipeline();
      const poll = setInterval(async () => {
        try {
          const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765"}/api/pipeline/status`);
          const status = await res.json();
          if (status.running) {
            const done = (status.results || []).length;
            const current = status.current_source || "...";
            const newSoFar = (status.results || []).reduce((s: number, r: { new?: number }) => s + (r.new || 0), 0);
            setPipelineStatus(`Fetching ${current}... (${done} sources done, ${newSoFar} new)`);
          } else {
            clearInterval(poll);
            const results = status.results || [];
            const totalNew = results.reduce((sum: number, r: { new?: number }) => sum + (r.new || 0), 0);
            const errors = results.filter((r: { error?: string }) => r.error).length;
            setPipelineStatus(`Done! ${totalNew} new items${errors ? `, ${errors} sources failed` : ""}`);
            loadItems(searchText || undefined);
            setTimeout(() => setPipelineStatus(null), 8000);
          }
        } catch {}
      }, 2000);
      setTimeout(() => clearInterval(poll), 300000);
    } catch {
      setPipelineStatus("Error starting pipeline");
      setTimeout(() => setPipelineStatus(null), 3000);
    }
  };

  const scoreColor = (score: number | null) => {
    if (score === null) return "bg-gray-700 text-gray-300";
    if (score > 0.7) return "bg-green-900/60 text-green-300 border border-green-700/50";
    if (score >= 0.4) return "bg-yellow-900/60 text-yellow-300 border border-yellow-700/50";
    return "bg-gray-800 text-gray-400 border border-gray-700/50";
  };

  return (
    <div className="p-6">
      <header className="border-b border-[var(--sidebar-border)] pb-4 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <FileText size={20} className="text-[var(--accent)]" />
              Feed
            </h2>
            <p className="text-xs text-[var(--muted)] mt-1">
              {total} items in your research feed
            </p>
          </div>
          <button
            onClick={handleRunPipeline}
            disabled={pipelineStatus === "running"}
            className="flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:opacity-50 text-white text-sm rounded-lg px-4 py-2 transition-colors"
          >
            {pipelineStatus === "running" ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Play size={16} />
            )}
            {pipelineStatus === "running"
              ? "Running..."
              : pipelineStatus
              ? pipelineStatus
              : "Run Pipeline"}
          </button>
        </div>
      </header>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]"
          />
          <input
            type="text"
            value={searchText}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder="Search items..."
            className="w-full bg-[var(--input-bg)] border border-[var(--card-border)] rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:border-[var(--accent)] transition-colors placeholder:text-[var(--muted)]"
          />
        </div>

        <div className="flex gap-2">
          {/* Sort Toggle */}
          <div className="flex rounded-lg border border-[var(--card-border)] overflow-hidden">
            <button
              onClick={() => setSortMode("recent")}
              className={`px-3 py-2 text-xs font-medium transition-colors ${
                sortMode === "recent"
                  ? "bg-[var(--accent)] text-white"
                  : "bg-[var(--input-bg)] text-[var(--muted)] hover:text-[var(--foreground)]"
              }`}
            >
              Recent
            </button>
            <button
              onClick={() => setSortMode("relevant")}
              className={`px-3 py-2 text-xs font-medium transition-colors ${
                sortMode === "relevant"
                  ? "bg-[var(--accent)] text-white"
                  : "bg-[var(--input-bg)] text-[var(--muted)] hover:text-[var(--foreground)]"
              }`}
            >
              Relevant
            </button>
          </div>

          {/* Source Filter */}
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="bg-[var(--input-bg)] border border-[var(--card-border)] rounded-lg px-3 py-2 text-xs text-[var(--foreground)] focus:outline-none focus:border-[var(--accent)]"
          >
            <option value="">All Sources</option>
            {sources.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="rounded-xl border border-red-800/50 bg-red-900/20 p-4 mb-6">
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 size={24} className="animate-spin text-[var(--accent)]" />
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && items.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20">
          <FileText size={48} className="text-[var(--muted)] mb-4" />
          <h3 className="text-lg font-medium mb-1">No items yet</h3>
          <p className="text-sm text-[var(--muted)]">
            Run the pipeline to start collecting research items.
          </p>
        </div>
      )}

      {/* Item Cards */}
      {!loading && (
        <div className="space-y-3">
          {items.map((item) => (
            <div
              key={item.id}
              className="rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-5 transition-colors hover:border-[var(--accent)]/30"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  {/* Title — links to detail page */}
                  <a
                    href={`/item/${item.id}`}
                    className="text-sm font-medium hover:text-[var(--accent)] transition-colors inline-flex items-center gap-1.5"
                  >
                    {item.title}
                  </a>

                  {/* Authors */}
                  {item.authors && item.authors.length > 0 && (
                    <p className="text-xs text-[var(--muted)] mt-1">
                      {item.authors.slice(0, 3).join(", ")}
                      {item.authors.length > 3 && ` +${item.authors.length - 3} more`}
                    </p>
                  )}

                  {/* Badges */}
                  <div className="flex items-center gap-2 mt-2">
                    {item.venue && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--accent)]/15 text-[var(--accent)] border border-[var(--accent)]/20">
                        {item.venue}
                      </span>
                    )}
                    {item.relevance_score !== null && (
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full ${scoreColor(
                          item.relevance_score
                        )}`}
                      >
                        {(item.relevance_score * 100).toFixed(0)}% relevant
                      </span>
                    )}
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--input-bg)] text-[var(--muted)] border border-[var(--card-border)]">
                      {item.source}
                    </span>
                  </div>

                  {/* Summary or abstract fallback */}
                  {item.summary ? (
                    <p className="text-xs text-[var(--muted)] mt-3 leading-relaxed line-clamp-3">
                      {item.summary}
                    </p>
                  ) : item.abstract ? (
                    <p className="text-xs text-[var(--muted)]/60 mt-3 leading-relaxed line-clamp-2 italic">
                      {item.abstract.slice(0, 200)}...
                    </p>
                  ) : null}
                </div>

                {/* Feedback Buttons */}
                <div className="flex flex-col gap-1.5 flex-shrink-0">
                  <button
                    onClick={() => handleFeedback(item.id, "liked")}
                    className={`flex items-center gap-1 px-2 py-1.5 rounded-lg text-[10px] transition-all ${
                      feedbackIds[item.id] === "liked"
                        ? "bg-green-900/40 text-green-400 scale-105"
                        : "bg-[var(--input-bg)] text-[var(--muted)] hover:text-green-400 hover:bg-green-900/20"
                    }`}
                    title="More like this — boosts similar papers in future"
                  >
                    <ThumbsUp size={12} />
                    {feedbackIds[item.id] === "liked" ? "Saved" : ""}
                  </button>
                  <button
                    onClick={() => handleFeedback(item.id, "hidden")}
                    className={`flex items-center gap-1 px-2 py-1.5 rounded-lg text-[10px] transition-all ${
                      feedbackIds[item.id] === "hidden"
                        ? "bg-red-900/40 text-red-400"
                        : "bg-[var(--input-bg)] text-[var(--muted)] hover:text-red-400 hover:bg-red-900/20"
                    }`}
                    title="Not relevant — reduces similar papers in future"
                  >
                    <EyeOff size={12} />
                    {feedbackIds[item.id] === "hidden" ? "Hidden" : ""}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
