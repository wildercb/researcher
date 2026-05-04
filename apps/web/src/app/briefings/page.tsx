"use client";

import { useState } from "react";
import { Newspaper, Sparkles, AlertCircle } from "lucide-react";

export default function BriefingsPage() {
  const [showMessage, setShowMessage] = useState(false);

  const handleGenerate = () => {
    setShowMessage(true);
  };

  return (
    <div className="p-6">
      <header className="border-b border-[var(--sidebar-border)] pb-4 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Newspaper size={20} className="text-[var(--accent)]" />
              Briefings
            </h2>
            <p className="text-xs text-[var(--muted)] mt-1">
              AI-generated summaries of your research landscape
            </p>
          </div>
          <button
            onClick={handleGenerate}
            className="flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white text-sm rounded-lg px-4 py-2 transition-colors"
          >
            <Sparkles size={16} />
            Generate Briefing
          </button>
        </div>
      </header>

      {/* LLM Key Message */}
      {showMessage && (
        <div className="rounded-xl border border-yellow-800/50 bg-yellow-900/20 p-4 mb-6 flex items-start gap-3">
          <AlertCircle size={18} className="text-yellow-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-yellow-200 font-medium">LLM API key required</p>
            <p className="text-xs text-yellow-300/70 mt-1">
              To generate briefings, configure your LLM API key in the server environment variables (OPENAI_API_KEY or ANTHROPIC_API_KEY). Once set, briefings will be generated automatically.
            </p>
          </div>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {/* Daily briefing placeholder */}
        <div className="rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-6">
          <h3 className="text-sm font-medium mb-2">Daily Briefing</h3>
          <p className="text-xs text-[var(--muted)]">
            Daily and weekly briefings will appear here once your research seeds are configured and the pipeline is running.
          </p>
        </div>

        {/* Weekly briefing placeholder */}
        <div className="rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-6">
          <h3 className="text-sm font-medium mb-2">Weekly Digest</h3>
          <p className="text-xs text-[var(--muted)]">
            A weekly summary of key developments, emerging trends, and notable papers across your research areas.
          </p>
        </div>
      </div>

      {/* Future briefing display area */}
      <div className="mt-6 rounded-xl border border-dashed border-[var(--card-border)] bg-[var(--card-bg)]/50 p-8 flex items-center justify-center min-h-[200px]">
        <p className="text-sm text-[var(--muted)] text-center">
          Generated briefings will appear here
        </p>
      </div>
    </div>
  );
}
