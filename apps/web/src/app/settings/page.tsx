"use client";

import { useState, useEffect } from "react";
import { Settings, Check, Loader2, Cpu, Cloud, Zap, Bot } from "lucide-react";
import { fetchSettings, updateProvider, type SettingsData, type ProviderInfo } from "@/lib/api";

const PROVIDER_ICONS: Record<string, typeof Cpu> = {
  "claude-code": Zap,
  "ollama": Cpu,
  "anthropic": Bot,
  "openai": Cloud,
};

const PROVIDER_ORDER = ["claude-code", "ollama", "anthropic", "openai"];

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<Record<string, string>>({});
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchSettings();
        setSettings(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load settings");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSwitch = async (provider: string) => {
    setSwitching(provider);
    setError(null);
    setSuccess(null);
    try {
      const model = selectedModel[provider];
      const result = await updateProvider(provider, model);
      setSuccess(`Switched to ${provider}${result.model ? ` (${result.model})` : ""}`);
      const data = await fetchSettings();
      setSettings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to switch provider");
    } finally {
      setSwitching(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 size={24} className="animate-spin text-[var(--accent)]" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <header className="border-b border-[var(--sidebar-border)] pb-4 mb-6">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Settings size={20} className="text-[var(--accent)]" />
          Settings
        </h2>
        <p className="text-xs text-[var(--muted)] mt-1">
          Choose your LLM provider for chat, summaries, and enrichment
        </p>
      </header>

      {/* Success / Error messages */}
      {success && (
        <div className="rounded-xl border border-green-800/50 bg-green-900/20 p-4 mb-6 flex items-center gap-2">
          <Check size={16} className="text-green-400" />
          <p className="text-sm text-green-300">{success}</p>
        </div>
      )}
      {error && (
        <div className="rounded-xl border border-red-800/50 bg-red-900/20 p-4 mb-6">
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {/* Current provider */}
      {settings && (
        <div className="rounded-xl border border-[var(--accent)]/30 bg-[var(--accent)]/5 p-4 mb-6">
          <p className="text-sm">
            <span className="text-[var(--muted)]">Current provider:</span>{" "}
            <span className="font-medium text-[var(--accent)]">{settings.current_provider}</span>
            <span className="text-[var(--muted)]"> — </span>
            <span className="text-xs font-mono text-[var(--muted)]">{settings.current_model}</span>
          </p>
        </div>
      )}

      {/* Provider cards */}
      <div className="space-y-4">
        {PROVIDER_ORDER.map((providerId) => {
          const provider = settings?.providers[providerId];
          if (!provider) return null;
          const Icon = PROVIDER_ICONS[providerId] || Cloud;
          const isActive = settings?.current_provider === providerId;
          const isSwitching = switching === providerId;
          const models = (provider as ProviderInfo & { models?: string[] }).models;

          return (
            <div
              key={providerId}
              className={`rounded-xl border p-5 transition-colors ${
                isActive
                  ? "border-[var(--accent)]/50 bg-[var(--accent)]/5"
                  : "border-[var(--card-border)] bg-[var(--card-bg)] hover:border-[var(--accent)]/30"
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${isActive ? "bg-[var(--accent)]/20 text-[var(--accent)]" : "bg-[var(--input-bg)] text-[var(--muted)]"}`}>
                    <Icon size={20} />
                  </div>
                  <div>
                    <h3 className="text-sm font-medium flex items-center gap-2">
                      {provider.label}
                      {isActive && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--accent)]/20 text-[var(--accent)]">
                          Active
                        </span>
                      )}
                    </h3>
                    <p className="text-xs text-[var(--muted)] mt-1">{provider.description}</p>

                    {/* Model selector for providers with choices */}
                    {models && models.length > 0 && (
                      <select
                        value={selectedModel[providerId] || models[0]}
                        onChange={(e) => setSelectedModel({ ...selectedModel, [providerId]: e.target.value })}
                        className="mt-3 bg-[var(--input-bg)] border border-[var(--card-border)] rounded-lg px-3 py-1.5 text-xs text-[var(--foreground)] focus:outline-none focus:border-[var(--accent)]"
                      >
                        {models.map((m: string) => (
                          <option key={m} value={m}>{m}</option>
                        ))}
                      </select>
                    )}

                    {provider.requires_key && (
                      <p className="text-[10px] text-yellow-400/70 mt-2">
                        Requires {provider.key_env} environment variable
                      </p>
                    )}
                  </div>
                </div>

                {!isActive && (
                  <button
                    onClick={() => handleSwitch(providerId)}
                    disabled={!!isSwitching}
                    className="flex items-center gap-1.5 bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:opacity-50 text-white text-xs rounded-lg px-4 py-2 transition-colors flex-shrink-0"
                  >
                    {isSwitching ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : (
                      <Check size={14} />
                    )}
                    {isSwitching ? "Switching..." : "Use this"}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Help text */}
      <div className="mt-8 rounded-xl border border-dashed border-[var(--card-border)] p-5">
        <h4 className="text-sm font-medium mb-2">How providers work</h4>
        <ul className="text-xs text-[var(--muted)] space-y-2">
          <li><strong className="text-[var(--foreground)]">Claude Code</strong> — Your Claude Code subscription powers enrichment. Run <code className="bg-[var(--input-bg)] px-1 rounded">/enrich-items</code> in Claude Code to generate summaries. Chat falls back to Ollama.</li>
          <li><strong className="text-[var(--foreground)]">Ollama</strong> — Free, local models. Run <code className="bg-[var(--input-bg)] px-1 rounded">ollama serve</code> first. Quality varies by model size.</li>
          <li><strong className="text-[var(--foreground)]">Anthropic</strong> — Best quality. Set <code className="bg-[var(--input-bg)] px-1 rounded">export ANTHROPIC_API_KEY=sk-ant-...</code> before starting the server.</li>
          <li><strong className="text-[var(--foreground)]">OpenAI</strong> — Set <code className="bg-[var(--input-bg)] px-1 rounded">export OPENAI_API_KEY=sk-...</code> before starting the server.</li>
        </ul>
      </div>
    </div>
  );
}
