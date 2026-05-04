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

export async function fetchHealth(): Promise<{ status: string }> {
  return request<{ status: string }>("/health");
}

export async function fetchItems(
  endpoint: string,
  params?: Record<string, string>
): Promise<unknown[]> {
  const query = params
    ? "?" + new URLSearchParams(params).toString()
    : "";
  return request<unknown[]>(`/${endpoint}${query}`);
}

export async function sendChat(message: string): Promise<{
  reply: string;
  sources?: string[];
}> {
  return request("/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}
