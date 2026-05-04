const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

// Health
export async function fetchHealth(): Promise<{ status: string; mode: string }> {
  return request("/api/health");
}

// Items
export interface ItemData {
  id: number;
  title: string;
  abstract: string | null;
  source: string;
  kind: string;
  authors: string[];
  venue: string | null;
  published_at: string | null;
  url: string;
  pdf_url: string | null;
  doi: string | null;
  arxiv_id: string | null;
  tags: string[];
  relevance_score: number | null;
  summary: string | null;
  enrichment_status: string;
}

export async function fetchItems(params?: {
  q?: string;
  source?: string;
  kind?: string;
  sort?: string;
  limit?: number;
}): Promise<{ items: ItemData[]; total: number }> {
  const searchParams = new URLSearchParams();
  if (params?.q) searchParams.set("q", params.q);
  if (params?.source) searchParams.set("source", params.source);
  if (params?.kind) searchParams.set("kind", params.kind);
  if (params?.sort) searchParams.set("sort", params.sort);
  if (params?.limit) searchParams.set("limit", String(params.limit));
  const qs = searchParams.toString();
  return request(`/api/items/${qs ? `?${qs}` : ""}`);
}

export async function sendFeedback(itemId: number, signal: string): Promise<void> {
  await request(`/api/items/${itemId}/feedback`, {
    method: "POST",
    body: JSON.stringify({ signal }),
  });
}

// Seeds
export interface SeedData {
  id: number;
  type: string;
  identifier: string;
  label: string;
  weight: number;
  is_negative: boolean;
}

export async function fetchSeeds(): Promise<{ seeds: SeedData[] }> {
  return request("/api/seeds/");
}

export async function addSeed(seed: { type: string; identifier: string; weight?: number }): Promise<{ id: number }> {
  return request("/api/seeds/", { method: "POST", body: JSON.stringify(seed) });
}

export async function deleteSeed(id: number): Promise<void> {
  await request(`/api/seeds/${id}`, { method: "DELETE" });
}

// Chat
export interface ConversationSummary {
  id: number;
  title: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface ChatResponse {
  response: string;
  agent: string | null;
  intent?: string;
  model: string | null;
  cost_usd: number;
  conversation_id: number;
}

export async function sendChat(
  messages: { content: string; role: string }[],
  conversationId?: number,
): Promise<ChatResponse> {
  return request("/api/chat/", {
    method: "POST",
    body: JSON.stringify({ messages, conversation_id: conversationId }),
  });
}

export async function fetchConversations(): Promise<{ conversations: ConversationSummary[] }> {
  return request("/api/chat/conversations/");
}

export async function fetchConversation(id: number): Promise<{
  id: number; title: string;
  messages: { id: number; role: string; content: string; agent: string | null; cost_usd: number; created_at: string | null }[];
}> {
  return request(`/api/chat/conversations/${id}`);
}

export async function deleteConversation(id: number): Promise<void> {
  await request(`/api/chat/conversations/${id}`, { method: "DELETE" });
}

// Trends
export interface TrendData {
  topic: string;
  count: number;
  recent_count: number;
  velocity: number;
}

export async function fetchTrends(): Promise<{ trends: TrendData[] }> {
  return request("/api/trends/");
}

// Calibrate
export async function triggerCalibrate(depth?: number, maxItems?: number): Promise<{ status: string }> {
  return request("/api/calibrate/", {
    method: "POST",
    body: JSON.stringify({ depth: depth || 1, max_items: maxItems || 500 }),
  });
}

// Pipeline
export async function triggerPipeline(source?: string): Promise<{ status: string }> {
  return request("/api/pipeline/run", { method: "POST", body: JSON.stringify({ source }) });
}

// Settings
export interface ProviderInfo {
  label: string;
  description: string;
  requires_key: boolean;
  key_env: string | null;
  models?: string[];
}

export interface SettingsData {
  current_provider: string;
  current_model: string;
  providers: Record<string, ProviderInfo>;
}

export async function fetchSettings(): Promise<SettingsData> {
  return request("/api/settings/");
}

export async function updateProvider(provider: string, model?: string): Promise<{ status: string; model: string }> {
  return request("/api/settings/provider", {
    method: "POST",
    body: JSON.stringify({ provider, model }),
  });
}
