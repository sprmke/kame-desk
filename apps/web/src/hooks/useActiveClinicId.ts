import { useSyncExternalStore } from "react";
import { getActiveClinicSnapshot, subscribeActiveClinic } from "@/lib/auth";

export function useActiveClinicId() {
  return useSyncExternalStore(
    subscribeActiveClinic,
    getActiveClinicSnapshot,
    () => null,
  );
}
