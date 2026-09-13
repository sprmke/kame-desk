import type { QueryClient } from "@tanstack/react-query";
import { getAccessToken, getClinicId } from "@/lib/auth";

export type WsConnectionState =
  "connecting" | "connected" | "polling" | "disconnected";

import { API_WS_BASE } from "@/lib/apiBase";

export function nextBackoffMs(
  attempt: number,
  base = 1000,
  max = 30000,
): number {
  return Math.min(max, base * 2 ** attempt);
}

export function shouldUsePolling(
  state: WsConnectionState,
  failedAttempts: number,
  threshold = 2,
): boolean {
  return state === "polling" || failedAttempts >= threshold;
}

export type NotificationWsPayload = {
  notification_id: string;
  type: string;
  title: string;
  body: string | null;
  href: string | null;
  actor_user_id: string | null;
  created_at: string;
  updated?: boolean;
};

type Options = {
  queryClient: QueryClient;
  onStateChange?: (state: WsConnectionState) => void;
  onNotification?: (payload: NotificationWsPayload) => void;
};

export class ClinicRealtimeClient {
  private socket: WebSocket | null = null;
  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private attempts = 0;
  private state: WsConnectionState = "disconnected";

  constructor(private readonly options: Options) {}

  start() {
    this.connect();
  }

  stop() {
    this.setState("disconnected");
    this.socket?.close();
    this.socket = null;
    if (this.pollTimer) clearInterval(this.pollTimer);
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.pollTimer = null;
    this.reconnectTimer = null;
  }

  getState() {
    return this.state;
  }

  private setState(next: WsConnectionState) {
    this.state = next;
    this.options.onStateChange?.(next);
  }

  private connect() {
    const clinicId = getClinicId();
    const token = getAccessToken();
    if (!clinicId || !token) return;

    this.setState("connecting");
    const url = `${API_WS_BASE}/ws/clinic/${clinicId}?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(url);
    this.socket = ws;

    ws.onopen = () => {
      this.attempts = 0;
      this.setState("connected");
      if (this.pollTimer) {
        clearInterval(this.pollTimer);
        this.pollTimer = null;
      }
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data as string) as {
          event?: string;
          data?: NotificationWsPayload;
        };
        if (payload.event?.startsWith("appointment.")) {
          this.options.queryClient.invalidateQueries({
            queryKey: ["waiting-room"],
          });
          this.options.queryClient.invalidateQueries({
            queryKey: ["appointments"],
          });
        }
        if (
          payload.event?.startsWith("notification.") &&
          payload.data?.notification_id
        ) {
          this.options.queryClient.invalidateQueries({
            queryKey: ["notifications"],
          });
          this.options.onNotification?.(payload.data);
        }
      } catch {
        /* ignore malformed payloads */
      }
    };

    ws.onclose = () => {
      this.socket = null;
      this.attempts += 1;
      if (shouldUsePolling(this.state, this.attempts)) {
        this.startPolling();
      }
      this.scheduleReconnect();
    };

    ws.onerror = () => {
      ws.close();
    };
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    const delay = nextBackoffMs(this.attempts);
    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }

  private startPolling() {
    if (this.pollTimer) return;
    this.setState("polling");
    this.options.queryClient.invalidateQueries({ queryKey: ["waiting-room"] });
    this.options.queryClient.invalidateQueries({ queryKey: ["notifications"] });
    this.pollTimer = setInterval(() => {
      this.options.queryClient.invalidateQueries({
        queryKey: ["waiting-room"],
      });
      this.options.queryClient.invalidateQueries({
        queryKey: ["notifications"],
      });
    }, 5000);
  }
}
