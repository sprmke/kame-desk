import { useCallback, useRef, useState } from "react";
import { getAccessToken, getClinicId } from "@/lib/auth";
import {
  applySoapDraftField,
  parseSseChunk,
  type SoapDraftSseEvent,
} from "@/features/soap/lib/soapDraftSse";

import { API_BASE } from "@/lib/apiBase";

type DraftFieldHandler = (field: string, value: string) => void;

export function useSoapDraftStream(appointmentId: string) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setIsStreaming(false);
  }, []);

  const start = useCallback(
    async (inputText: string, onField: DraftFieldHandler) => {
      cancel();
      setError(null);
      setIsStreaming(true);
      const controller = new AbortController();
      abortRef.current = controller;

      const token = getAccessToken();
      const clinicId = getClinicId();

      try {
        const res = await fetch(
          `${API_BASE}/appointments/${appointmentId}/soap-draft`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
              ...(clinicId ? { "X-Clinic-Id": clinicId } : {}),
            },
            body: JSON.stringify({ input_text: inputText }),
            signal: controller.signal,
          },
        );

        if (!res.ok) {
          const body = await res.json().catch(() => null);
          const message =
            body?.detail ??
            (res.status === 429
              ? "AI drafting unavailable today"
              : "Draft failed");
          setError(typeof message === "string" ? message : "Draft failed");
          return;
        }

        if (!res.body) {
          setError("Draft failed");
          return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const parsed = parseSseChunk(buffer);
          buffer = parsed.remainder;

          for (const event of parsed.events) {
            if (event.type === "field") {
              onField(event.field, event.value);
            } else if (event.type === "error") {
              setError(event.message);
            }
          }
        }

        const tail = parseSseChunk(buffer);
        for (const event of tail.events) {
          if (event.type === "field") {
            onField(event.field, event.value);
          } else if (event.type === "error") {
            setError(event.message);
          }
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setError("Draft failed");
        }
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [appointmentId, cancel],
  );

  return { start, cancel, isStreaming, error };
}

export { applySoapDraftField, type SoapDraftSseEvent };
