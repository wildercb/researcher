"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Plus, Trash2, MessageSquare, Loader2 } from "lucide-react";
import {
  sendChat,
  fetchConversations,
  fetchConversation,
  deleteConversation,
  type ConversationSummary,
} from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string | null;
  cost?: number;
}

export default function ChatPage() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConvoId, setActiveConvoId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load conversation list
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const data = await fetchConversations();
      setConversations(data.conversations);
    } catch {}
  };

  const loadConversation = async (id: number) => {
    try {
      const data = await fetchConversation(id);
      setActiveConvoId(id);
      setMessages(
        data.messages.map((m) => ({
          id: String(m.id),
          role: m.role as "user" | "assistant",
          content: m.content,
          agent: m.agent,
          cost: m.cost_usd,
        }))
      );
      setError(null);
    } catch {}
  };

  const handleNewChat = () => {
    setActiveConvoId(null);
    setMessages([]);
    setError(null);
  };

  const handleDeleteConvo = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConvoId === id) handleNewChat();
    } catch {}
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    setError(null);

    const userMessage: Message = { id: Date.now().toString(), role: "user", content: input.trim() };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput("");
    setIsLoading(true);

    try {
      const chatMessages = updatedMessages.map((m) => ({ content: m.content, role: m.role }));
      const result = await sendChat(chatMessages, activeConvoId ?? undefined);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: result.response,
        agent: result.agent,
        cost: result.cost_usd,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      if (result.conversation_id) {
        setActiveConvoId(result.conversation_id);
        loadConversations();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get response");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen">
      {/* Conversation sidebar */}
      <div className="w-56 border-r border-[var(--sidebar-border)] flex flex-col bg-[var(--sidebar-bg)] hidden md:flex">
        <div className="p-3 border-b border-[var(--sidebar-border)]">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white text-xs rounded-lg px-3 py-2 transition-colors"
          >
            <Plus size={14} /> New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto py-1">
          {conversations.map((c) => (
            <div
              key={c.id}
              onClick={() => loadConversation(c.id)}
              className={`group flex items-center justify-between px-3 py-2 mx-1 rounded-lg cursor-pointer text-xs transition-colors ${
                activeConvoId === c.id
                  ? "bg-[var(--accent)]/10 text-[var(--accent)]"
                  : "text-[var(--muted)] hover:bg-white/5 hover:text-[var(--foreground)]"
              }`}
            >
              <div className="flex items-center gap-2 min-w-0">
                <MessageSquare size={12} className="flex-shrink-0" />
                <span className="truncate">{c.title}</span>
              </div>
              <button
                onClick={(e) => handleDeleteConvo(c.id, e)}
                className="opacity-0 group-hover:opacity-100 text-[var(--muted)] hover:text-red-400 p-0.5"
              >
                <Trash2 size={11} />
              </button>
            </div>
          ))}
          {conversations.length === 0 && (
            <p className="text-[10px] text-[var(--muted)] text-center py-4">No conversations yet</p>
          )}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        <header className="border-b border-[var(--sidebar-border)] px-6 py-4">
          <h2 className="text-lg font-semibold">Atlas Chat</h2>
          <p className="text-xs text-[var(--muted)]">
            {activeConvoId ? `Conversation #${activeConvoId}` : "New conversation"}
          </p>
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md">
                <h3 className="text-2xl font-bold text-[var(--accent)] mb-2">Atlas</h3>
                <p className="text-[var(--muted)] text-sm">
                  Ask about your research, get briefings, explore ideas. Conversations are saved automatically.
                </p>
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
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
                <Loader2 size={16} className="animate-spin text-[var(--accent)]" />
              </div>
            </div>
          )}

          {error && (
            <div className="flex justify-start">
              <div className="max-w-[70%] rounded-xl px-4 py-3 text-sm bg-red-900/30 border border-red-800/50 text-red-300">
                {error}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

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
    </div>
  );
}
