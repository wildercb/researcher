"use client";

import { useState, useEffect } from "react";
import { Sprout, Plus, Trash2, Zap, Loader2 } from "lucide-react";
import { fetchSeeds, addSeed, deleteSeed, triggerCalibrate, type SeedData } from "@/lib/api";

const SEED_TYPES = ["paper", "author", "venue", "keyword"];

export default function SeedsPage() {
  const [seeds, setSeeds] = useState<SeedData[]>([]);
  const [loading, setLoading] = useState(true);
  const [newType, setNewType] = useState("paper");
  const [newIdentifier, setNewIdentifier] = useState("");
  const [adding, setAdding] = useState(false);
  const [calibrating, setCalibrating] = useState(false);

  const loadSeeds = async () => {
    try {
      const data = await fetchSeeds();
      setSeeds(data.seeds);
    } catch {
      // API not available
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadSeeds(); }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newIdentifier.trim()) return;
    setAdding(true);
    try {
      await addSeed({ type: newType, identifier: newIdentifier.trim() });
      setNewIdentifier("");
      await loadSeeds();
    } catch {}
    setAdding(false);
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteSeed(id);
      setSeeds(seeds.filter(s => s.id !== id));
    } catch {}
  };

  const handleCalibrate = async () => {
    setCalibrating(true);
    try {
      await triggerCalibrate(1, 500);
    } catch {}
    setTimeout(() => setCalibrating(false), 3000);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <header className="border-b border-[var(--sidebar-border)] pb-4 mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Sprout size={20} className="text-[var(--accent)]" />
            Seeds
          </h2>
          <p className="text-xs text-[var(--muted)] mt-1">Seeds calibrate Atlas to your research interests</p>
        </div>
        <button onClick={handleCalibrate} disabled={calibrating || seeds.length === 0}
          className="flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:opacity-40 text-white text-sm rounded-lg px-4 py-2 transition-colors">
          {calibrating ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
          {calibrating ? "Calibrating..." : "Calibrate"}
        </button>
      </header>

      <form onSubmit={handleAdd} className="flex gap-2 mb-6">
        <select value={newType} onChange={e => setNewType(e.target.value)}
          className="bg-[var(--input-bg)] border border-[var(--card-border)] rounded-lg px-3 py-2 text-sm">
          {SEED_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <input type="text" value={newIdentifier} onChange={e => setNewIdentifier(e.target.value)}
          placeholder={newType === "paper" ? "DOI, arXiv ID, or title..." : newType === "author" ? "Author name..." : newType === "venue" ? "Venue name..." : "Keyword..."}
          className="flex-1 bg-[var(--input-bg)] border border-[var(--card-border)] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]" />
        <button type="submit" disabled={adding || !newIdentifier.trim()}
          className="flex items-center gap-1 bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:opacity-40 text-white text-sm rounded-lg px-4 py-2 transition-colors">
          <Plus size={16} /> Add
        </button>
      </form>

      {loading ? (
        <div className="text-center py-8 text-[var(--muted)] text-sm">Loading seeds...</div>
      ) : seeds.length === 0 ? (
        <div className="rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-8 text-center">
          <Sprout size={40} className="mx-auto text-[var(--muted)] mb-3" />
          <h3 className="text-sm font-medium mb-1">No seeds yet</h3>
          <p className="text-xs text-[var(--muted)] max-w-sm mx-auto">Add papers, authors, venues, or keywords to start.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {seeds.map(seed => (
            <div key={seed.id} className="flex items-center justify-between rounded-lg border border-[var(--card-border)] bg-[var(--card-bg)] px-4 py-3">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-[var(--accent)]/10 text-[var(--accent)]">{seed.type}</span>
                <span className="text-sm">{seed.identifier}</span>
                {seed.is_negative && <span className="text-xs text-red-400 bg-red-400/10 px-1.5 py-0.5 rounded">negative</span>}
              </div>
              <button onClick={() => handleDelete(seed.id)} className="text-[var(--muted)] hover:text-red-400 transition-colors p-1">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
