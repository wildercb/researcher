"use client";

import { useState, useEffect } from "react";
import { Newspaper, Sparkles, Loader2, Zap, Brain, FileText } from "lucide-react";
import { fetchBriefings, generateBriefing, type BriefingData } from "@/lib/api";

type BriefingMode = "basic" | "deep" | "claude-code";

export default function BriefingsPage() {
  const [briefings, setBriefings] = useState<BriefingData[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [mode, setMode] = useState<BriefingMode>("basic");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { loadBriefings(); }, []);

  const loadBriefings = async () => {
    try {
      const data = await fetchBriefings();
      setBriefings(data.briefings);
    } catch {} finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const result = await generateBriefing("daily", mode);
      if ((result as unknown as { error?: string }).error) {
        setError((result as unknown as { error: string }).error);
      } else if ((result as unknown as { mode?: string }).mode === "claude-code") {
        setError("Claude Code mode: ask your Claude Code agent 'generate a deep briefing for me' and it will analyze your papers and save the result here.");
      } else {
        setBriefings((prev) => [result, ...prev]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate briefing");
    } finally {
      setGenerating(false);
    }
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
          <div className="flex items-center gap-2">
            <div className="flex rounded-lg border border-[var(--card-border)] overflow-hidden">
              <button onClick={() => setMode("basic")} className={`flex items-center gap-1 px-3 py-1.5 text-[10px] font-medium transition-colors ${mode === "basic" ? "bg-[var(--accent)] text-white" : "bg-[var(--input-bg)] text-[var(--muted)]"}`}>
                <FileText size={11} /> Basic
              </button>
              <button onClick={() => setMode("deep")} className={`flex items-center gap-1 px-3 py-1.5 text-[10px] font-medium transition-colors ${mode === "deep" ? "bg-[var(--accent)] text-white" : "bg-[var(--input-bg)] text-[var(--muted)]"}`}>
                <Brain size={11} /> Deep
              </button>
              <button onClick={() => setMode("claude-code")} className={`flex items-center gap-1 px-3 py-1.5 text-[10px] font-medium transition-colors ${mode === "claude-code" ? "bg-[var(--accent)] text-white" : "bg-[var(--input-bg)] text-[var(--muted)]"}`}>
                <Zap size={11} /> Claude Code
              </button>
            </div>
            <button onClick={handleGenerate} disabled={generating} className="flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:opacity-50 text-white text-sm rounded-lg px-4 py-2 transition-colors">
              {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />} Generate
            </button>
          </div>
        </div>
      </header>

      <div className="rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-4 mb-6 text-xs text-[var(--muted)]">
        {mode === "basic" && "Basic: structured summary from item data. No LLM needed."}
        {mode === "deep" && "Deep: LLM analyzes papers for trends, gaps, research ideas, and venue targets. Uses Ollama or API key."}
        {mode === "claude-code" && "Claude Code: say 'generate a deep briefing' to your Claude Code agent — it reads papers and writes analysis with its own intelligence."}
      </div>

      {error && (
        <div className="rounded-xl border border-yellow-800/50 bg-yellow-900/20 p-4 mb-6">
          <p className="text-sm text-yellow-300">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20"><Loader2 size={24} className="animate-spin text-[var(--accent)]" /></div>
      ) : briefings.length === 0 ? (
        <div className="rounded-xl border border-dashed border-[var(--card-border)] p-8 text-center">
          <Newspaper size={40} className="mx-auto text-[var(--muted)] mb-3" />
          <h3 className="text-sm font-medium mb-1">No briefings yet</h3>
          <p className="text-xs text-[var(--muted)]">Click Generate to create one.</p>
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
            </div>
            {b.must_read_count > 0 && (
              <div className="flex items-center gap-3 text-xs text-[var(--muted)]">
                <span>{b.must_read_count} must-read</span>
                <span>{b.on_radar_count} on radar</span>
              </div>
            )}
          </div>
          <div className="prose prose-invert prose-sm max-w-none text-[var(--foreground)] [&_h1]:text-lg [&_h1]:font-bold [&_h1]:mb-3 [&_h2]:text-base [&_h2]:font-semibold [&_h2]:mt-5 [&_h2]:mb-2 [&_h3]:text-sm [&_h3]:font-medium [&_h3]:mt-3 [&_a]:text-[var(--accent)] [&_a]:no-underline [&_a:hover]:underline [&_li]:text-xs [&_p]:text-xs [&_p]:leading-relaxed [&_strong]:text-[var(--foreground)]"
            dangerouslySetInnerHTML={{ __html: markdownToHtml(b.content) }} />
        </div>
      ))}
    </div>
  );
}

function markdownToHtml(md: string): string {
  return md
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^# (.*$)/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/^- (.*$)/gm, '<li>$1</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
}
