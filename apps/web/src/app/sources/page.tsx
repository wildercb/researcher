"use client";

import { useState, useEffect } from "react";
import { Radio, Plus, Rss, Globe, Search, Loader2 } from "lucide-react";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765";

interface SourceInfo {
  name: string;
  enabled: boolean;
  cadence: string;
}

export default function SourcesPage() {
  const [sources, setSources] = useState<SourceInfo[]>([]);
  const [config, setConfig] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(true);
  const [addType, setAddType] = useState<"rss" | "web" | "query">("rss");
  const [addName, setAddName] = useState("");
  const [addUrl, setAddUrl] = useState("");
  const [adding, setAdding] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    try {
      const [srcRes, cfgRes] = await Promise.all([
        fetch(`${BASE_URL}/api/sources/`).then(r => r.json()),
        fetch(`${BASE_URL}/api/sources/config`).then(r => r.json()),
      ]);
      setSources(srcRes.sources || []);
      setConfig(cfgRes.config || {});
    } catch {} finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addUrl.trim()) return;
    setAdding(true);
    setSuccess(null);
    try {
      let endpoint = "";
      let body = {};
      if (addType === "rss") {
        endpoint = "/api/sources/rss/add";
        body = { name: addName || addUrl, url: addUrl };
      } else if (addType === "web") {
        endpoint = "/api/sources/web-monitor/add";
        body = { name: addName || addUrl, url: addUrl };
      } else {
        endpoint = "/api/sources/semantic-scholar/add-query";
        body = { query: addUrl };
      }
      const res = await fetch(`${BASE_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      setSuccess(`Added: ${data.name || data.query || addUrl}`);
      setAddUrl("");
      setAddName("");
      loadSources();
    } catch {} finally {
      setAdding(false);
    }
  };

  const rssFeeds = ((config as Record<string, { feeds?: { name: string; url: string }[] }>).rss?.feeds) || [];
  const s2Queries = ((config as Record<string, { queries?: string[] }>).semantic_scholar?.queries) || [];
  const webMonitors = ((config as Record<string, { urls?: { name: string; url: string }[] }>).web_monitor?.urls) || [];

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <header className="border-b border-[var(--sidebar-border)] pb-4 mb-6">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Radio size={20} className="text-[var(--accent)]" />
          Sources
        </h2>
        <p className="text-xs text-[var(--muted)] mt-1">
          Configure where Atlas looks for research — feeds, websites, queries
        </p>
      </header>

      {/* Add new source */}
      <div className="rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] p-5 mb-6">
        <h3 className="text-sm font-medium mb-3">Add a Source</h3>
        <form onSubmit={handleAdd} className="space-y-3">
          <div className="flex gap-2">
            <button type="button" onClick={() => setAddType("rss")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-colors ${addType === "rss" ? "bg-[var(--accent)] text-white" : "bg-[var(--input-bg)] text-[var(--muted)]"}`}>
              <Rss size={12} /> RSS Feed
            </button>
            <button type="button" onClick={() => setAddType("web")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-colors ${addType === "web" ? "bg-[var(--accent)] text-white" : "bg-[var(--input-bg)] text-[var(--muted)]"}`}>
              <Globe size={12} /> Website
            </button>
            <button type="button" onClick={() => setAddType("query")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-colors ${addType === "query" ? "bg-[var(--accent)] text-white" : "bg-[var(--input-bg)] text-[var(--muted)]"}`}>
              <Search size={12} /> S2 Query
            </button>
          </div>
          <div className="flex gap-2">
            {addType !== "query" && (
              <input type="text" value={addName} onChange={e => setAddName(e.target.value)}
                placeholder="Name (optional)" className="w-48 bg-[var(--input-bg)] border border-[var(--card-border)] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]" />
            )}
            <input type="text" value={addUrl} onChange={e => setAddUrl(e.target.value)}
              placeholder={addType === "query" ? "Search query..." : "URL..."}
              className="flex-1 bg-[var(--input-bg)] border border-[var(--card-border)] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]" />
            <button type="submit" disabled={adding || !addUrl.trim()}
              className="flex items-center gap-1 bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:opacity-40 text-white text-sm rounded-lg px-4 py-2 transition-colors">
              {adding ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />} Add
            </button>
          </div>
        </form>
        {success && <p className="text-xs text-green-400 mt-2">{success}</p>}
      </div>

      {/* Registered sources */}
      <h3 className="text-sm font-medium mb-3">Active Sources</h3>
      {loading ? (
        <Loader2 size={20} className="animate-spin text-[var(--accent)]" />
      ) : (
        <div className="grid gap-2 mb-6">
          {sources.map(s => (
            <div key={s.name} className="flex items-center justify-between rounded-lg border border-[var(--card-border)] bg-[var(--card-bg)] px-4 py-3">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${s.enabled ? "bg-green-400" : "bg-gray-600"}`} />
                <span className="text-sm font-mono">{s.name}</span>
              </div>
              <span className="text-xs text-[var(--muted)]">{s.cadence || "—"}</span>
            </div>
          ))}
        </div>
      )}

      {/* RSS feeds detail */}
      {rssFeeds.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium mb-2">RSS Feeds ({rssFeeds.length})</h3>
          <div className="space-y-1">
            {rssFeeds.map((f, i) => (
              <div key={i} className="flex items-center justify-between text-xs px-3 py-2 rounded-lg bg-[var(--card-bg)] border border-[var(--card-border)]">
                <span className="font-medium">{f.name}</span>
                <span className="text-[var(--muted)] truncate ml-3 max-w-[300px]">{f.url}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* S2 queries */}
      {s2Queries.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium mb-2">Semantic Scholar Queries ({s2Queries.length})</h3>
          <div className="flex flex-wrap gap-2">
            {s2Queries.map((q, i) => (
              <span key={i} className="text-xs px-3 py-1 rounded-full bg-[var(--input-bg)] border border-[var(--card-border)]">{q}</span>
            ))}
          </div>
        </div>
      )}

      {/* Web monitors */}
      {webMonitors.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium mb-2">Web Monitors ({webMonitors.length})</h3>
          <div className="space-y-1">
            {webMonitors.map((u, i) => (
              <div key={i} className="flex items-center justify-between text-xs px-3 py-2 rounded-lg bg-[var(--card-bg)] border border-[var(--card-border)]">
                <span className="font-medium">{u.name}</span>
                <span className="text-[var(--muted)] truncate ml-3 max-w-[300px]">{u.url}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
