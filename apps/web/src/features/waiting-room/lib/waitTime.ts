import { useEffect, useState } from "react";
import type { WaitingRoomItem } from "./waitingRoom";

export type WaitUrgency = "normal" | "delayed" | "overdue";

export interface WaitTimeStats {
  elapsedMinutes: number;
  formatted: string;
  urgency: WaitUrgency;
  isEarly: boolean;
}

export function computeWaitStats(
  scheduledStart: string,
  now: Date = new Date(),
): WaitTimeStats {
  const start = new Date(scheduledStart);
  const diffMs = now.getTime() - start.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);

  if (diffMinutes < 0) {
    const futureMinutes = Math.abs(diffMinutes);
    return {
      elapsedMinutes: 0,
      formatted: `${futureMinutes}m early`,
      urgency: "normal",
      isEarly: true,
    };
  }

  const hours = Math.floor(diffMinutes / 60);
  const mins = diffMinutes % 60;
  const formatted = hours > 0 ? `${hours}h ${mins}m wait` : `${mins}m wait`;

  let urgency: WaitUrgency = "normal";
  if (diffMinutes >= 30) {
    urgency = "overdue";
  } else if (diffMinutes >= 15) {
    urgency = "delayed";
  }

  return {
    elapsedMinutes: diffMinutes,
    formatted,
    urgency,
    isEarly: false,
  };
}

/** Tick every 15s so Arrived wait badges stay current without heavy re-renders. */
export function useLiveTimer(intervalMs: number = 15000) {
  const [now, setNow] = useState<Date>(() => new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setNow(new Date());
    }, intervalMs);
    return () => clearInterval(timer);
  }, [intervalMs]);

  return now;
}

export function sortArrivedByLongestWait(
  items: WaitingRoomItem[],
  now: Date = new Date(),
): WaitingRoomItem[] {
  return [...items].sort((a, b) => {
    const statsA = computeWaitStats(a.scheduled_start, now);
    const statsB = computeWaitStats(b.scheduled_start, now);
    return statsB.elapsedMinutes - statsA.elapsedMinutes;
  });
}

export function doctorsFromQueue(items: WaitingRoomItem[]) {
  const map = new Map<string, { id: string; name: string; count: number }>();
  for (const item of items) {
    const existing = map.get(item.doctor_id);
    if (existing) {
      existing.count += 1;
    } else {
      map.set(item.doctor_id, {
        id: item.doctor_id,
        name: item.doctor_name?.trim() || "Doctor",
        count: 1,
      });
    }
  }
  return [...map.values()].sort((a, b) => a.name.localeCompare(b.name));
}

export function filterByDoctor(
  items: WaitingRoomItem[],
  doctorId: string | "all",
): WaitingRoomItem[] {
  if (doctorId === "all") return items;
  return items.filter((item) => item.doctor_id === doctorId);
}
