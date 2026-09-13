import { useNavigate } from "@tanstack/react-router";
import { Bell } from "lucide-react";
import { useState } from "react";

import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotificationsList,
  useNotificationsUnreadCount,
} from "@/features/notifications/hooks/useNotifications";
import {
  formatRelativeTime,
  notificationIconFor,
} from "@/features/notifications/lib/notificationsDisplay";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { useIsBelowLg } from "@/hooks/useMediaQuery";
import { cn } from "@/lib/utils";

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const isMobile = useIsBelowLg();
  const navigate = useNavigate();
  const { data: unread } = useNotificationsUnreadCount();
  const { data, isPending: isLoading } = useNotificationsList({
    page: 1,
    enabled: open,
  });
  const markRead = useMarkNotificationRead();
  const markAll = useMarkAllNotificationsRead();

  const badge = unread?.unread_count ?? data?.unread_count ?? 0;
  const capped = unread?.unread_capped ?? data?.unread_capped ?? false;
  const label =
    capped && badge >= 99 ? "99+" : badge > 0 ? String(badge) : null;

  function openRow(href: string | null, id: string, isRead: boolean) {
    if (!isRead) markRead.mutate(id);
    setOpen(false);
    if (href) navigate({ to: href });
  }

  const list = (
    <div className="flex max-h-[min(24rem,70dvh)] flex-col">
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <span className="text-sm font-medium">Alerts</span>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-8"
          disabled={!badge}
          onClick={() => markAll.mutate()}
        >
          Mark all read
        </Button>
      </div>
      <ul className="overflow-y-auto">
        {isLoading ? (
          <li className="px-3 py-6 text-center text-sm text-muted-foreground">
            Loading…
          </li>
        ) : null}
        {!isLoading && (data?.items.length ?? 0) === 0 ? (
          <li className="px-3 py-6 text-center text-sm text-muted-foreground">
            No alerts
          </li>
        ) : null}
        {data?.items.map((row) => {
          const Icon = notificationIconFor(row.type);
          return (
            <li key={row.id}>
              <button
                type="button"
                className={cn(
                  "flex w-full gap-3 px-3 py-3 text-left transition-colors hover:bg-secondary/60",
                  !row.is_read && "bg-primary/5",
                )}
                onClick={() => openRow(row.href, row.id, row.is_read)}
              >
                <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <Icon className="size-4" aria-hidden />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex items-start justify-between gap-2">
                    <span className="text-sm font-medium">{row.title}</span>
                    <span className="shrink-0 text-xs text-muted-foreground tabular-nums">
                      {formatRelativeTime(row.created_at)}
                    </span>
                  </span>
                  {row.body ? (
                    <span className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                      {row.body}
                    </span>
                  ) : null}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
      <div className="border-t border-border p-2">
        <Button
          type="button"
          variant="ghost"
          className="w-full"
          onClick={() => {
            setOpen(false);
            navigate({ to: "/dashboard/notifications" });
          }}
        >
          View all
        </Button>
      </div>
    </div>
  );

  const triggerClass =
    "relative flex size-11 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground";

  const bellIcon = (
    <>
      <Bell className="size-5" />
      {label ? (
        <span className="absolute right-1 top-1 flex min-w-[1.125rem] items-center justify-center rounded-full bg-primary px-1 text-[10px] font-semibold text-primary-foreground">
          {label}
        </span>
      ) : null}
    </>
  );

  if (isMobile) {
    return (
      <>
        <button
          type="button"
          className={triggerClass}
          aria-label={label ? `${label} unread alerts` : "Alerts"}
          onClick={() => setOpen(true)}
        >
          {bellIcon}
        </button>
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetContent side="bottom" className="rounded-t-xl p-0">
            <SheetTitle className="sr-only">Alerts</SheetTitle>
            {list}
          </SheetContent>
        </Sheet>
      </>
    );
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={triggerClass}
          aria-label={label ? `${label} unread alerts` : "Alerts"}
        >
          {bellIcon}
        </button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-80 p-0">
        {list}
      </PopoverContent>
    </Popover>
  );
}
