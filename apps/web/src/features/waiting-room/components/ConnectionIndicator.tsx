import { cn } from "@/lib/utils";
import type { WsConnectionState } from "@/lib/websocket";

const LABELS: Record<WsConnectionState, string> = {
  connected: "Live",
  connecting: "Reconnecting",
  polling: "Polling",
  disconnected: "Offline",
};

export function ConnectionIndicator({ state }: { state: WsConnectionState }) {
  const tone =
    state === "connected"
      ? "bg-success"
      : state === "polling" || state === "connecting"
        ? "bg-warning"
        : "bg-muted-foreground";

  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
      <span className={cn("size-2 rounded-full", tone)} aria-hidden />
      {LABELS[state]}
    </span>
  );
}
