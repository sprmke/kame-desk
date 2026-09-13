import { useState } from "react";
import { Send as SendIcon, X } from "lucide-react";
import { AssistantMark } from "@/components/brand/AssistantMark";
import { useAssistantChat } from "@/features/assistant/hooks/useAssistantChat";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { aboveBottomTabBarClassName } from "@/components/mobile/BottomTabBar";
import { cn } from "@/lib/utils";

function formatProposal(
  proposal: Record<string, unknown> | undefined,
  tool: string,
) {
  if (!proposal || Object.keys(proposal).length === 0) {
    return tool.replaceAll("_", " ");
  }
  const parts = Object.entries(proposal)
    .filter(([, value]) => value !== null && value !== undefined)
    .map(([key, value]) => `${key.replaceAll("_", " ")}: ${String(value)}`);
  return parts.join(" · ");
}

function ResultCard({ result }: { result: Record<string, unknown> }) {
  const name = String(result.patient_name ?? result.full_name ?? "");
  const start = String(result.scheduled_start ?? "");
  const invoice = String(result.invoice_number ?? result.invoice_id ?? "");
  const balance = result.balance_due ?? result.total;
  if (!name && !start && !invoice && balance == null) return null;
  return (
    <div className="mt-2 rounded-lg border border-border bg-card p-3 text-left text-foreground">
      {name ? <p className="font-medium">{name}</p> : null}
      {start ? (
        <p className="text-xs text-muted-foreground">
          {new Date(start).toLocaleString("en-PH", { timeZone: "Asia/Manila" })}
        </p>
      ) : null}
      {invoice ? (
        <p className="text-xs text-muted-foreground">{invoice}</p>
      ) : null}
      {balance != null ? (
        <p className="text-xs text-muted-foreground">PHP {String(balance)}</p>
      ) : null}
    </div>
  );
}

export function AssistantPanel({ onClose }: { onClose: () => void }) {
  const { messages, send, isStreaming, error, confirmAction, cancelAction } =
    useAssistantChat();
  const [draft, setDraft] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = draft.trim();
    if (!text || isStreaming) return;
    setDraft("");
    await send(text);
  }

  return (
    <div
      id="clinic-assistant-panel"
      className={cn(
        "fixed right-4 z-50 flex h-[min(70vh,560px)] w-[min(92vw,400px)] flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-theme-lg",
        aboveBottomTabBarClassName(),
      )}
      role="dialog"
      aria-label="Clinic assistant"
      aria-modal="true"
    >
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <span className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <AssistantMark className="size-4 text-primary" />
          Clinic assistant
        </span>
        <button
          type="button"
          className="flex size-11 items-center justify-center rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground"
          onClick={onClose}
          aria-label="Close"
        >
          <X className="size-4" />
        </button>
      </div>
      <div
        className="flex-1 space-y-3 overflow-y-auto p-4 text-sm"
        aria-live="polite"
        aria-relevant="additions"
      >
        {messages.length === 0 && (
          <div className="flex flex-col gap-2">
            <p className="text-muted-foreground">
              Ask about patients, appointments, or balances.
            </p>
            <div className="flex flex-wrap gap-2">
              {[
                "Who is on the calendar today?",
                "Check this patient's balance",
                "Cancel the next appointment",
              ].map((prompt) => (
                <Button
                  key={prompt}
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={() => void send(prompt)}
                >
                  {prompt}
                </Button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m) => (
          <div
            key={m.id}
            className={cn("flex", m.role === "user" && "justify-end")}
          >
            <div
              className={cn(
                "max-w-[85%] rounded-xl px-3 py-2",
                m.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-foreground",
              )}
            >
              <p className="whitespace-pre-wrap">{m.content}</p>
              {m.toolResults?.map((event) => {
                if (event.type !== "tool_result") return null;
                return <ResultCard key={event.tool} result={event.result} />;
              })}
              {m.pendingActions?.map((action) => {
                if (action.type !== "confirm_card") return null;
                return (
                  <div
                    key={action.action_id}
                    className="mt-2 rounded-lg border-2 border-foreground bg-background p-3 text-left text-foreground"
                  >
                    <p className="text-sm font-semibold">Confirm this action</p>
                    <p className="mb-3 mt-1 text-sm">
                      {formatProposal(action.proposal, action.tool)}
                    </p>
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        size="sm"
                        onClick={() => confirmAction(action.action_id)}
                      >
                        {action.external_send ? "Send" : "Confirm"}
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => cancelAction(action.action_id)}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
        {error ? (
          <div className="flex items-center justify-between gap-2 text-destructive">
            <p>{error}</p>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => {
                const lastUser = [...messages]
                  .reverse()
                  .find((m) => m.role === "user");
                if (lastUser) void send(lastUser.content);
              }}
            >
              Retry
            </Button>
          </div>
        ) : null}
      </div>
      <form className="border-t border-border p-3" onSubmit={onSubmit}>
        <div className="flex gap-2">
          <Input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Ask the assistant"
            disabled={isStreaming}
          />
          <Button
            type="submit"
            size="icon"
            disabled={isStreaming || !draft.trim()}
          >
            <SendIcon />
          </Button>
        </div>
      </form>
    </div>
  );
}
