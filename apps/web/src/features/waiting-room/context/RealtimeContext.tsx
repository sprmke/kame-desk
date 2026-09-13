import { createContext, useContext } from "react";
import { useClinicRealtime } from "@/features/waiting-room/hooks/useClinicRealtime";
import type { WsConnectionState } from "@/lib/websocket";

const RealtimeContext = createContext<WsConnectionState>("disconnected");

export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const state = useClinicRealtime();
  return (
    <RealtimeContext.Provider value={state}>
      {children}
    </RealtimeContext.Provider>
  );
}

export function useRealtimeState() {
  return useContext(RealtimeContext);
}
