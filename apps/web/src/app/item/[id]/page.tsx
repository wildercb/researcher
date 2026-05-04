"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { ArrowLeft, ExternalLink, ThumbsUp, EyeOff, Loader2 } from "lucide-react";
import Link from "next/link";
import { type ItemData, sendFeedback } from "@/lib/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765";

export default function ItemDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [item, setItem] = useState<ItemData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`${BASE_URL}/api/items/${id}`);
        const data = await res.json();
        setItem(data);
      } catch {
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 size={24} className="animate-spin text-[var(--accent)]" />
      </div>
    );
  }

  if (!item || !item.title) {
    return (
      <div className="p-6">
        <p className="text-sm text-[var(--muted)]">Item not found.</p>
      </div>
    );
  }

  const scoreColor =
    (item.relevance_score ?? 0) > 0.7
      ? "bg-green-900/60 text-green-300 border-green-700/50"
      : (item.relevance_score ?? 0) >= 0.4
      ? "bg-yellow-900/60 text-yellow-300 border-yellow-700/50"
      : "bg-gray-800 text-gray-400 border-gray-700/50";

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <Link
        href="/feed"
        className="inline-flex items-center gap-1 text-xs text-[var(--muted)] hover:text-[var(--accent)] mb-4"
      >
        <ArrowLeft size={14} /> Back to Feed
      </Link>

      <h1 className="text-xl font-bold leading-tight mb-3">{item.title}</h1>

      <div className="flex flex-wrap items-center gap-2 mb-4">
        {item.authors.length > 0 && (
          <span className="text-sm text-[var(--muted)]">{item.authors.join(", ")}</span>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-6">
        {item.venue && (
          <span className="text-xs px-2 py-1 rounded-full bg-[var(--accent)]/15 text-[var(--accent)]">
            {item.venue}
          </span>
        )}
        <span className="text-xs px-2 py-1 rounded-full bg-[var(--input-bg)] text-[var(--muted)]">
          {item.source}
        </span>
        <span className="text-xs px-2 py-1 rounded-full bg-[var(--input-bg)] text-[var(--muted)]">
          {item.kind}
        </span>
        {item.relevance_score !== null && (
          <span className={`text-xs px-2 py-1 rounded-full border ${scoreColor}`}>
            {(item.relevance_score * 100).toFixed(0)}% relevant
          </span>
        )}
        {item.published_at && (
          <span className="text-xs text-[var(--muted)]">
            {new Date(item.published_at).toLocaleDateString()}
          </span>
        )}
      </div>

      {/* Summary */}
      {item.summary && (
        <div className="rounded-xl border border-[var(--accent)]/30 bg-[var(--accent)]/5 p-4 mb-6">
          <h3 className="text-xs font-medium text-[var(--accent)] mb-1">Summary</h3>
          <p className="text-sm leading-relaxed">{item.summary}</p>
        </div>
      )}

      {/* Abstract */}
      {item.abstract && (
        <div className="rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-4 mb-6">
          <h3 className="text-xs font-medium text-[var(--muted)] mb-2">Abstract</h3>
          <p className="text-sm leading-relaxed text-[var(--foreground)]">{item.abstract}</p>
        </div>
      )}

      {/* Tags */}
      {item.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-6">
          {item.tags.map((tag) => (
            <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--input-bg)] text-[var(--muted)]">
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-3 mb-6">
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white text-sm rounded-lg px-4 py-2 transition-colors"
        >
          <ExternalLink size={14} /> Open Paper
        </a>
        {item.pdf_url && (
          <a
            href={item.pdf_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 border border-[var(--card-border)] text-sm rounded-lg px-4 py-2 hover:border-[var(--accent)] transition-colors"
          >
            PDF
          </a>
        )}
        <button
          onClick={() => sendFeedback(item.id, "liked")}
          className="p-2 rounded-lg bg-[var(--input-bg)] text-[var(--muted)] hover:text-green-400 hover:bg-green-900/20 transition-colors"
        >
          <ThumbsUp size={16} />
        </button>
        <button
          onClick={() => sendFeedback(item.id, "hidden")}
          className="p-2 rounded-lg bg-[var(--input-bg)] text-[var(--muted)] hover:text-red-400 hover:bg-red-900/20 transition-colors"
        >
          <EyeOff size={16} />
        </button>
      </div>

      {/* IDs */}
      <div className="text-[10px] text-[var(--muted)] space-y-1">
        {item.doi && <p>DOI: {item.doi}</p>}
        {item.arxiv_id && <p>arXiv: {item.arxiv_id}</p>}
        <p>Source: {item.source} / {item.enrichment_status}</p>
      </div>
    </div>
  );
}
