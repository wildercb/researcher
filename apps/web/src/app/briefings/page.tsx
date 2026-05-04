import { Newspaper } from "lucide-react";

export default function BriefingsPage() {
  return (
    <div className="p-6">
      <header className="border-b border-[var(--sidebar-border)] pb-4 mb-6">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Newspaper size={20} className="text-[var(--accent)]" />
          Briefings
        </h2>
        <p className="text-xs text-[var(--muted)] mt-1">
          AI-generated summaries of your research landscape
        </p>
      </header>

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
    </div>
  );
}
