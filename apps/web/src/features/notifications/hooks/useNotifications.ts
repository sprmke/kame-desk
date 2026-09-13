import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";

export const NOTIFICATIONS_KEY = "notifications";

export function useNotificationsList(params?: {
  page?: number;
  unread_only?: boolean;
  /** The header bell defers the list until the panel opens. */
  enabled?: boolean;
}) {
  return useQuery({
    queryKey: [
      NOTIFICATIONS_KEY,
      params?.page ?? 1,
      params?.unread_only ?? false,
    ],
    queryFn: () =>
      api.listStaffNotifications({
        page: params?.page ?? 1,
        page_size: 20,
        unread_only: params?.unread_only,
      }),
    enabled: params?.enabled ?? true,
  });
}

export function useNotificationsUnreadCount() {
  return useQuery({
    queryKey: [NOTIFICATIONS_KEY, "unread-count"],
    queryFn: () => api.staffNotificationsUnreadCount(),
    refetchInterval: (query) => {
      const state = query.state.data;
      return state ? false : 30000;
    },
  });
}

export function useMarkNotificationRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.markStaffNotificationRead(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [NOTIFICATIONS_KEY] });
    },
  });
}

export function useMarkAllNotificationsRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.markAllStaffNotificationsRead(),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [NOTIFICATIONS_KEY] });
    },
  });
}
