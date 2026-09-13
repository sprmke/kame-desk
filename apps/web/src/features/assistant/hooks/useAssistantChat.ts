import { useCallback, useRef, useState } from "react";
import { getAccessToken, getClinicId } from "@/lib/auth";
import { api } from "@/lib/apiClient";
import {
  parseAssistantSseChunk,
  type AssistantSseEvent,
} from "@/features/assistant/lib/assistantSse";

import { API_BASE } from "@/lib/apiBase";

function pathnamePatientId(pathname: string): string | undefined {
  const match = pathname.match(/\/patients\/([^/]+)/);
  const id = match?.[1];
  if (!id || id === "new") return undefined;
  return id;
}

function pathnameAppointmentId(pathname: string): string | undefined {
  const match = pathname.match(/\/appointments\/([^/]+)/);
  const id = match?.[1];
  if (!id || id === "new" || id === "calendar") return undefined;
  return id;
}

export type AssistantMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  pendingActions?: AssistantSseEvent[];
  toolResults?: AssistantSseEvent[];
};

export function useAssistantChat() {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<AssistantMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const ensureConversation = useCallback(
    async (clinicId: string) => {
      if (conversationId) return conversationId;
      const row = await api.createAssistantConversation();
      setConversationId(row.id);
      return row.id;
    },
    [conversationId],
  );

  const send = useCallback(
    async (content: string) => {
      const clinicId = getClinicId();
      if (!clinicId) {
        setError("Clinic not selected");
        return;
      }
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setError(null);
      setIsStreaming(true);

      const userMsg: AssistantMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content,
      };
      setMessages((prev) => [...prev, userMsg]);

      try {
        const convId = await ensureConversation(clinicId);
        const token = getAccessToken();
        const res = await fetch(
          `${API_BASE}/assistant/conversations/${convId}/messages`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
              "X-Clinic-Id": clinicId,
            },
            body: JSON.stringify({
              content,
              page_context: {
                route: window.location.pathname,
                patient_id: pathnamePatientId(window.location.pathname),
                appointment_id: pathnameAppointmentId(window.location.pathname),
              },
            }),
            signal: controller.signal,
          },
        );

        if (!res.ok) {
          const body = await res.json().catch(() => null);
          const message =
            typeof body?.detail === "string" ? body.detail : "Request failed";
          setError(message);
          return;
        }

        if (!res.body) {
          setError("Request failed");
          return;
        }

        let assistantText = "";
        const pending: AssistantSseEvent[] = [];
        const toolResults: AssistantSseEvent[] = [];
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const parsed = parseAssistantSseChunk(buffer);
          buffer = parsed.remainder;
          for (const event of parsed.events) {
            if (event.type === "text") assistantText = event.content;
            if (event.type === "confirm_card") pending.push(event);
            if (event.type === "tool_result") toolResults.push(event);
            if (event.type === "error") setError(event.message);
          }
        }

        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: assistantText || "Done.",
            pendingActions: pending,
            toolResults,
          },
        ]);
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setError("Request failed");
        }
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [ensureConversation],
  );

  const confirmAction = useCallback(async (actionId: string) => {
    await api.confirmAssistantAction(actionId);
    setMessages((prev) =>
      prev.map((m) => ({
        ...m,
        pendingActions: m.pendingActions?.filter(
          (a) => a.type !== "confirm_card" || a.action_id !== actionId,
        ),
      })),
    );
  }, []);

  const cancelAction = useCallback(async (actionId: string) => {
    await api.cancelAssistantAction(actionId);
    setMessages((prev) =>
      prev.map((m) => ({
        ...m,
        pendingActions: m.pendingActions?.filter(
          (a) => a.type !== "confirm_card" || a.action_id !== actionId,
        ),
      })),
    );
  }, []);

  return {
    messages,
    send,
    isStreaming,
    error,
    confirmAction,
    cancelAction,
  };
}
