"use client";

import { useState, useEffect, useCallback } from "react";
import { Newspaper, Sparkles, Loader2, Brain, FileText, Zap } from "lucide-react";
import { fetchBriefings, generateBriefing, type BriefingData } from "@/lib/api";

type BriefingMode = "basic" | "ollama" | "api" | "claude-code";

export default function BriefingsPage() {
  const [briefings, setBriefings] = useState<BriefingData[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [mode, setMode] = useState<BriefingMode>("api");
  const [error, setError] = useState<string | null>(null);

  const loadBriefings = useCallback(async () => {
    try {
      const data = await fetchBriefings();
      setBriefings(data.briefings);
    } catch {} finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadBriefings(); }, [loadBriefings]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const result = await generateBriefing("daily", mode);
      if ((result as unknown as { error?: string }).error) {
        setError((result as unknown as { error: string }).error);
        setGenerating(false);
        return;
      }
      // Add to list immediately
      setBriefings((prev) => [result, ...prev.filter(b => b.id !== result.id)]);

      // If generating in background (claude-code), poll until done
      if ((result as unknown as { generating?: boolean }).generating) {
        const pollId = setInterval(async () => {
          try {
            const updated = await fetchBriefings();
            const latest = updated.briefings.find(b => b.id === result.id);
            if (latest && !(latest as unknown as { generating?: boolean }).generating) {
              clearInterval(pollId);
              setBriefings(updated.briefings);
              setGenerating(false);
            }
          } catch {}
        }, 3000);
        // Safety: stop polling after 5 minutes
        setTimeout(() => { clearInterval(pollId); setGenerating(false); }, 300000);
        return;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate briefing");
    }
    setGenerating(false);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <header className="border-b border-[var(--sidebar-border)] pb-4 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Newspaper size={20} className="text-[var(--accent)]" />
              Briefings
            </h2>
            <p className="text-xs text-[var(--muted)] mt-1">Research analysis with trends, gaps, and paper ideas</p>
          </div>
          <button onClick={handleGenerate} disabled={generating} className="flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:opacity-50 text-white text-sm rounded-lg px-4 py-2 transition-colors">
            {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
            {generating ? "Generating..." : "Generate"}
          </button>
        </div>
      </header>

      {/* Mode selector */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button onClick={() => setMode("basic")} className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-colors border ${mode === "basic" ? "border-[var(--accent)] bg-[var(--accent)]/10 text-[var(--accent)]" : "border-[var(--card-border)] bg-[var(--card-bg)] text-[var(--muted)] hover:border-[var(--accent)]/30"}`}>
          <FileText size={13} /> Summary Only
        </button>
        <button onClick={() => setMode("ollama")} className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-colors border ${mode === "ollama" ? "border-[var(--accent)] bg-[var(--accent)]/10 text-[var(--accent)]" : "border-[var(--card-border)] bg-[var(--card-bg)] text-[var(--muted)] hover:border-[var(--accent)]/30"}`}>
          <Brain size={13} /> Ollama (Local)
        </button>
        <button onClick={() => setMode("api")} className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-colors border ${mode === "api" ? "border-[var(--accent)] bg-[var(--accent)]/10 text-[var(--accent)]" : "border-[var(--card-border)] bg-[var(--card-bg)] text-[var(--muted)] hover:border-[var(--accent)]/30"}`}>
          <Sparkles size={13} /> API (Anthropic/OpenAI)
        </button>
        <button onClick={() => setMode("claude-code")} className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-colors border ${mode === "claude-code" ? "border-[var(--accent)] bg-[var(--accent)]/10 text-[var(--accent)]" : "border-[var(--card-border)] bg-[var(--card-bg)] text-[var(--muted)] hover:border-[var(--accent)]/30"}`}>
          <Zap size={13} /> Claude Code
        </button>
      </div>

      <div className="rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-3 mb-6 text-xs text-[var(--muted)]">
        {mode === "basic" && "Paper listings with authors, venues, scores, topics. Instant, no LLM."}
        {mode === "ollama" && "Full analysis via local Ollama model (granite4:micro). Includes trends, gaps, research ideas. ~30s."}
        {mode === "api" && "Full analysis via Anthropic/OpenAI API. Best quality. Requires API key in environment."}
        {mode === "claude-code" && "Full analysis via your current LLM config. Generates in background — page auto-refreshes when done."}
      </div>

      {error && (
        <div className="rounded-xl border border-red-800/50 bg-red-900/20 p-4 mb-6">
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20"><Loader2 size={24} className="animate-spin text-[var(--accent)]" /></div>
      ) : briefings.length === 0 ? (
        <div className="rounded-xl border border-dashed border-[var(--card-border)] p-8 text-center">
          <Newspaper size={40} className="mx-auto text-[var(--muted)] mb-3" />
          <h3 className="text-sm font-medium mb-1">No briefings yet</h3>
          <p className="text-xs text-[var(--muted)]">Select a mode and click Generate.</p>
        </div>
      ) : null}

      {briefings.map((b) => (
        <div key={b.id} className="rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-6 mb-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-[var(--accent)]/10 text-[var(--accent)]">
                {(b as unknown as { mode?: string }).mode || b.period}
              </span>
              <span className="text-xs text-[var(--muted)]">{new Date(b.created_at).toLocaleDateString()}</span>
              {(b as unknown as { status?: string }).status === "generating" && (
                <span className="flex items-center gap-1 text-xs text-yellow-400">
                  <Loader2 size={12} className="animate-spin" /> Generating analysis...
                </span>
              )}
            </div>
            {b.must_read_count > 0 && (
              <div className="flex items-center gap-3 text-xs text-[var(--muted)]">
                <span>{b.must_read_count} must-read</span>
                <span>{b.on_radar_count} on radar</span>
              </div>
            )}
          </div>
          <div className="prose prose-invert prose-sm max-w-none text-[var(--foreground)] [&_h1]:text-lg [&_h1]:font-bold [&_h1]:mb-3 [&_h2]:text-base [&_h2]:font-semibold [&_h2]:mt-5 [&_h2]:mb-2 [&_h3]:text-sm [&_h3]:font-medium [&_h3]:mt-3 [&_a]:text-[var(--accent)] [&_a]:no-underline [&_a:hover]:underline [&_li]:text-xs [&_p]:text-xs [&_p]:leading-relaxed [&_strong]:text-[var(--foreground)] [&_table]:text-xs [&_th]:text-left [&_th]:px-2 [&_th]:py-1 [&_td]:px-2 [&_td]:py-1 [&_table]:border-collapse [&_th]:border-b [&_th]:border-[var(--card-border)] [&_td]:border-b [&_td]:border-[var(--card-border)]"
            dangerouslySetInnerHTML={{ __html: markdownToHtml(b.content) }} />
        </div>
      ))}
    </div>
  );
}

function markdownToHtml(md: string): string {
  let html = md
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^# (.*$)/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/^- (.*$)/gm, '<li>$1</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');

  // Basic table support
  html = html.replace(/\|(.+)\|/g, (match) => {
    const cells = match.split('|').filter(c => c.trim());
    if (cells.every(c => c.trim().match(/^[-:]+$/))) return ''; // separator row
    const tag = cells.some(c => c.trim().match(/^[-:]+$/)) ? 'th' : 'td';
    return '<tr>' + cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('') + '</tr>';
  });

  return html;
}
