import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
import { ApiError } from "@/lib/apiError";
import {
  listQueuedSoapDrafts,
  removeQueuedSoapDraft,
} from "@/lib/offlineSoapQueue";

/** Flushes any SOAP drafts queued while offline, oldest first. A network
 * failure (still offline, or a blip mid-sync) stops the loop so the next
 * "online" event or mount retries everything still queued. A server
 * rejection (4xx — e.g. the appointment was deleted while offline) can never
 * succeed on retry, so that entry is dropped and the loop continues rather
 * than jamming every draft queued after it. */
export async function flushQueuedSoapDrafts(): Promise<string[]> {
  const queued = await listQueuedSoapDrafts();
  const synced: string[] = [];
  for (const entry of queued) {
    try {
      await api.createSoapNote(entry.appointmentId, entry.body);
      await removeQueuedSoapDraft(entry.clientDraftToken);
      synced.push(entry.appointmentId);
    } catch (err) {
      if (err instanceof ApiError) {
        await removeQueuedSoapDraft(entry.clientDraftToken);
        continue;
      }
      break;
    }
  }
  return synced;
}

/** Mount once near the app root: flushes queued offline SOAP drafts on
 * reconnect and on initial mount (covers a reload that happens while still
 * offline, then comes back online later). */
export function useOfflineSoapSync() {
  const qc = useQueryClient();

  useEffect(() => {
    async function flush() {
      const appointmentIds = await flushQueuedSoapDrafts();
      for (const id of new Set(appointmentIds)) {
        qc.invalidateQueries({ queryKey: ["soap-notes", id] });
      }
    }
    void flush();
    window.addEventListener("online", flush);
    return () => window.removeEventListener("online", flush);
  }, [qc]);
}
