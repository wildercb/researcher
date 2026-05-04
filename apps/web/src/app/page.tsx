"use client";

import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import { sendChat } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string | null;
  cost?: number;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    setError(null);

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput("");
    setIsLoading(true);

    try {
      const chatMessages = updatedMessages.map((m) => ({
        content: m.content,
        role: m.role,
      }));

      const result = await sendChat(chatMessages);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: result.response,
        agent: result.agent,
        cost: result.cost_usd,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "An unexpected error occurred";
      setError(
        `Failed to get response: ${msg}. Please check that the API server is running and your API key is configured.`
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="border-b border-[var(--sidebar-border)] px-6 py-4">
        <h2 className="text-lg font-semibold">Atlas Chat</h2>
        <p className="text-xs text-[var(--muted)]">Ask anything about your research</p>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md">
              <h3 className="text-2xl font-bold text-[var(--accent)] mb-2">Atlas</h3>
              <p className="text-[var(--muted)] text-sm">
                Your AI research assistant. Ask questions, explore trends, and get briefings on the topics you care about.
              </p>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div className="max-w-[70%]">
              <div
                className={`rounded-xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-[var(--accent)] text-white"
                    : "bg-[var(--card-bg)] border border-[var(--card-border)]"
                }`}
              >
                {msg.content}
              </div>
              {msg.role === "assistant" && (msg.agent || msg.cost !== undefined) && (
                <p className="text-[10px] text-[var(--muted)] mt-1 px-1">
                  {msg.agent && <span>{msg.agent}</span>}
                  {msg.agent && msg.cost !== undefined && <span> &middot; </span>}
                  {msg.cost !== undefined && <span>${msg.cost.toFixed(4)}</span>}
                </p>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-xl px-4 py-3 text-sm">
              <span className="inline-flex gap-1">
                <span className="animate-pulse">.</span>
                <span className="animate-pulse" style={{ animationDelay: "0.2s" }}>.</span>
                <span className="animate-pulse" style={{ animationDelay: "0.4s" }}>.</span>
              </span>
            </div>
          </div>
        )}

        {error && (
          <div className="flex justify-start">
            <div className="max-w-[70%] rounded-xl px-4 py-3 text-sm leading-relaxed bg-red-900/30 border border-red-800/50 text-red-300">
              {error}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-[var(--sidebar-border)] px-6 py-4">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask Atlas..."
            className="flex-1 bg-[var(--input-bg)] border border-[var(--card-border)] rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-[var(--accent)] transition-colors placeholder:text-[var(--muted)]"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl px-4 py-3 transition-colors"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
