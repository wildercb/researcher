import { Sprout, Plus } from "lucide-react";

export default function SeedsPage() {
  return (
    <div className="p-6">
      <header className="border-b border-[var(--sidebar-border)] pb-4 mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Sprout size={20} className="text-[var(--accent)]" />
            Seeds
          </h2>
          <p className="text-xs text-[var(--muted)] mt-1">
            Manage your research seeds here
          </p>
        </div>
        <button className="flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white text-sm rounded-lg px-4 py-2 transition-colors">
          <Plus size={16} />
          Add Seed
        </button>
      </header>

      <div className="rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-8 text-center">
        <Sprout size={40} className="mx-auto text-[var(--muted)] mb-3" />
        <h3 className="text-sm font-medium mb-1">No seeds configured</h3>
        <p className="text-xs text-[var(--muted)] max-w-sm mx-auto">
          Seeds are the topics, keywords, and sources that Atlas monitors. Add seeds to start tracking research areas that matter to you.
        </p>
      </div>
    </div>
  );
}
