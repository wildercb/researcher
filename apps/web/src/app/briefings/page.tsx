"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Newspaper, Sparkles, Loader2, Brain, FileText, Zap, CheckCircle } from "lucide-react";
import { fetchBriefings, generateBriefing, type BriefingData } from "@/lib/api";

type BriefingMode = "basic" | "ollama" | "api" | "claude-code";

export default function BriefingsPage() {
  const [briefings, setBriefings] = useState<BriefingData[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [mode, setMode] = useState<BriefingMode>("claude-code");
  const [error, setError] = useState<string | null>(null);
  const [progressMsg, setProgressMsg] = useState<string | null>(null);
  const [newBriefingId, setNewBriefingId] = useState<number | null>(null);
  const topRef = useRef<HTMLDivElement>(null);

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
    setProgressMsg("Preparing paper listings...");
    setNewBriefingId(null);

    try {
      const result = await generateBriefing("daily", mode);

      if ((result as unknown as { error?: string }).error) {
        setError((result as unknown as { error: string }).error);
        setGenerating(false);
        setProgressMsg(null);
        return;
      }

      const resultId = result.id;

      // If background generating, poll for completion
      if ((result as unknown as { generating?: boolean }).generating) {
        setProgressMsg("Paper listings ready. LLM analyzing trends, gaps & ideas...");
        // Show the partial result immediately
        setBriefings((prev) => [result, ...prev.filter(b => b.id !== resultId)]);

        const pollId = setInterval(async () => {
          try {
            const updated = await fetchBriefings();
            const latest = updated.briefings.find(b => b.id === resultId);
            if (latest && !(latest as unknown as { generating?: boolean }).generating) {
              clearInterval(pollId);
              setBriefings(updated.briefings);
              setGenerating(false);
              setProgressMsg(null);
              setNewBriefingId(resultId);
              topRef.current?.scrollIntoView({ behavior: "smooth" });
              // Clear the "new" highlight after 10s
              setTimeout(() => setNewBriefingId(null), 10000);
            }
          } catch {}
        }, 3000);
        setTimeout(() => { clearInterval(pollId); setGenerating(false); setProgressMsg(null); }, 300000);
      } else {
        // Synchronous modes (basic, ollama, api)
        setBriefings((prev) => [result, ...prev]);
        setGenerating(false);
        setProgressMsg(null);
        setNewBriefingId(resultId);
        topRef.current?.scrollIntoView({ behavior: "smooth" });
        setTimeout(() => setNewBriefingId(null), 10000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate briefing");
      setGenerating(false);
      setProgressMsg(null);
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
          <button onClick={handleGenerate} disabled={generating} className="flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:opacity-50 text-white text-sm rounded-lg px-4 py-2 transition-colors">
            {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
            {generating ? "Generating..." : "Generate"}
          </button>
        </div>
      </header>

      {/* Mode selector */}
      <div className="flex flex-wrap gap-2 mb-4">
        {([
          { id: "basic" as BriefingMode, icon: FileText, label: "Summary Only", desc: "Instant, no LLM" },
          { id: "ollama" as BriefingMode, icon: Brain, label: "Ollama (Local)", desc: "~2-3 min" },
          { id: "api" as BriefingMode, icon: Sparkles, label: "API", desc: "Needs API key" },
          { id: "claude-code" as BriefingMode, icon: Zap, label: "Claude Code", desc: "~2-3 min" },
        ]).map(m => (
          <button key={m.id} onClick={() => setMode(m.id)} className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-colors border ${mode === m.id ? "border-[var(--accent)] bg-[var(--accent)]/10 text-[var(--accent)]" : "border-[var(--card-border)] bg-[var(--card-bg)] text-[var(--muted)] hover:border-[var(--accent)]/30"}`}>
            <m.icon size={13} /> {m.label}
          </button>
        ))}
      </div>

      {/* Progress banner */}
      {progressMsg && (
        <div className="rounded-xl border border-[var(--accent)]/30 bg-[var(--accent)]/5 p-4 mb-6 flex items-center gap-3">
          <Loader2 size={18} className="animate-spin text-[var(--accent)] flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-[var(--accent)]">{progressMsg}</p>
            <p className="text-[10px] text-[var(--muted)] mt-0.5">This may take 2-3 minutes. The page will update automatically.</p>
          </div>
        </div>
      )}

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

      <div ref={topRef} />

      {briefings.map((b) => {
        const isNew = b.id === newBriefingId;
        const isGenerating = (b as unknown as { generating?: boolean }).generating;
        return (
          <div key={b.id} className={`rounded-xl border p-6 mb-4 transition-all duration-500 ${
            isNew ? "border-[var(--accent)] bg-[var(--accent)]/5 ring-1 ring-[var(--accent)]/20" :
            isGenerating ? "border-yellow-700/30 bg-yellow-900/5" :
            "border-[var(--card-border)] bg-[var(--card-bg)]"
          }`}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                {isNew && <CheckCircle size={14} className="text-green-400" />}
                {isGenerating && <Loader2 size={14} className="animate-spin text-yellow-400" />}
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-[var(--accent)]/10 text-[var(--accent)]">
                  {(b as unknown as { mode?: string }).mode || b.period}
                </span>
                <span className="text-xs text-[var(--muted)]">{new Date(b.created_at).toLocaleDateString()}</span>
                {isNew && <span className="text-[10px] text-green-400 font-medium">NEW</span>}
                {isGenerating && <span className="text-[10px] text-yellow-400">Analyzing...</span>}
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
        );
      })}
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
    .replace(/\|(.+)\|/g, (match) => {
      const cells = match.split('|').filter(c => c.trim());
      if (cells.every(c => c.trim().match(/^[-:]+$/))) return '';
      return '<tr>' + cells.map(c => `<td style="padding:4px 8px;border-bottom:1px solid var(--card-border)">${c.trim()}</td>`).join('') + '</tr>';
    })
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
}
