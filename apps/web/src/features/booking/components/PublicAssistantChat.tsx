import { useState } from "react";
import { Send, X } from "lucide-react";
import { AssistantMark } from "@/components/brand/AssistantMark";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { API_BASE } from "@/lib/apiBase";

type Props = { slug: string };

export function PublicAssistantChat({ slug }: Props) {
  const [open, setOpen] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<
    Array<{ role: string; content: string }>
  >([]);
  const [pending, setPending] = useState(false);

  async function send() {
    const content = input.trim();
    if (!content || pending) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content }]);
    setPending(true);
    try {
      const res = await fetch(
        `${API_BASE}/public/clinics/${slug}/assistant/messages`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content, conversation_id: conversationId }),
        },
      );
      if (!res.ok || !res.body) throw new Error("Chat failed");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let assistant = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        for (const line of chunk.split("\n")) {
          if (!line.startsWith("data: ")) continue;
          const event = JSON.parse(line.slice(6)) as {
            type: string;
            content?: string;
            id?: string;
          };
          if (event.type === "conversation_id" && event.id) {
            setConversationId(event.id);
          }
          if (event.type === "text" && event.content) {
            assistant = event.content;
          }
        }
      }
      if (assistant) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: assistant },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Chat is unavailable. Use the booking form.",
        },
      ]);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="fixed bottom-4 right-4 z-20">
      {open && (
        <div className="mb-2 flex w-80 flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-theme-lg">
          <div className="flex items-center justify-between border-b border-border px-3 py-2">
            <span className="text-sm font-medium text-foreground">
              Ask a question
            </span>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="size-7"
              onClick={() => setOpen(false)}
            >
              <X className="size-4" />
            </Button>
          </div>
          <div className="flex max-h-64 flex-col gap-2 overflow-y-auto p-3 text-sm">
            {messages.length === 0 && (
              <p className="text-muted-foreground">
                Ask about hours, location, or availability.
              </p>
            )}
            {messages.map((m, i) => (
              <p
                key={i}
                className={
                  m.role === "user"
                    ? "self-end rounded-lg bg-primary px-3 py-1.5 text-primary-foreground"
                    : "self-start rounded-lg bg-secondary px-3 py-1.5 text-foreground"
                }
              >
                {m.content}
              </p>
            ))}
          </div>
          <div className="flex gap-2 border-t border-border p-2">
            <Input
              className="h-9"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && void send()}
            />
            <Button
              type="button"
              size="icon"
              className="size-9 shrink-0"
              disabled={pending}
              onClick={() => void send()}
            >
              <Send className="size-4" />
            </Button>
          </div>
        </div>
      )}
      <Button
        type="button"
        size="lg"
        className="rounded-full shadow-theme-lg"
        onClick={() => setOpen((v) => !v)}
      >
        <AssistantMark className="size-4" />
        Chat
      </Button>
    </div>
  );
}
