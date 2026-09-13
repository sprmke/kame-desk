import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { showNotificationToast } from "@/features/notifications/lib/NotificationToast";
import { useActiveClinicId } from "@/hooks/useActiveClinicId";
import { api } from "@/lib/apiClient";
import { ClinicRealtimeClient, type WsConnectionState } from "@/lib/websocket";

export function useClinicRealtime() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const clinicId = useActiveClinicId();
  const [state, setState] = useState<WsConnectionState>("disconnected");
  const clientRef = useRef<ClinicRealtimeClient | null>(null);
  const { data: me } = useQuery({
    queryKey: ["me", clinicId],
    queryFn: () => api.me(),
    enabled: Boolean(clinicId),
  });

  const handleNotification = useCallback(
    (
      payload: Parameters<
        NonNullable<
          ConstructorParameters<
            typeof ClinicRealtimeClient
          >[0]["onNotification"]
        >
      >[0],
    ) => {
      if (payload.actor_user_id && payload.actor_user_id === me?.id) {
        return;
      }
      showNotificationToast(payload, {
        onView: (row) => {
          if (row.href) navigate({ to: row.href });
        },
      });
    },
    [me?.id, navigate],
  );

  useEffect(() => {
    const client = new ClinicRealtimeClient({
      queryClient,
      onStateChange: setState,
      onNotification: handleNotification,
    });
    clientRef.current = client;
    client.start();
    return () => client.stop();
  }, [queryClient, handleNotification, clinicId]);

  return state;
}
