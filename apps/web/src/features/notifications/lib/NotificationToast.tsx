import { toast } from "sonner";

import {
  formatRelativeTime,
  notificationIconFor,
} from "@/features/notifications/lib/notificationsDisplay";
import { playArrivalChime } from "@/features/waiting-room/lib/arrivalChime";
import type { NotificationWsPayload } from "@/lib/websocket";

type Options = {
  onView?: (payload: NotificationWsPayload) => void;
};

export function showNotificationToast(
  payload: NotificationWsPayload,
  { onView }: Options = {},
) {
  if (payload.type === "visit.arrived") {
    playArrivalChime();
  }

  const Icon = notificationIconFor(payload.type);
  toast.message(payload.title, {
    id: payload.notification_id,
    icon: (
      <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
        <Icon className="size-4" aria-hidden />
      </span>
    ),
    description: payload.body ? (
      <span className="line-clamp-2 text-[13px] font-medium text-foreground/80">
        {payload.body}
      </span>
    ) : (
      <span className="text-xs text-muted-foreground">
        {formatRelativeTime(payload.created_at)}
      </span>
    ),
    action: onView
      ? {
          label: "Open",
          onClick: () => onView(payload),
        }
      : undefined,
  });
}
