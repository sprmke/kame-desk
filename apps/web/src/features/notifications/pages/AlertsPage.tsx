import { useEffect, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Bell, RefreshCw } from "lucide-react";

import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotificationsList,
} from "@/features/notifications/hooks/useNotifications";
import { usePushNotifications } from "@/features/notifications/hooks/usePushNotifications";
import {
  formatRelativeTime,
  notificationIconFor,
} from "@/features/notifications/lib/notificationsDisplay";
import { Button } from "@/components/ui/button";
import { PageContainer } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/EmptyState";
import { cn } from "@/lib/utils";

const VAPID_KEY = import.meta.env.VITE_VAPID_PUBLIC_KEY as string | undefined;

export function AlertsPage() {
  useEffect(() => {
    document.title = "Alerts · DoctorDesk";
  }, []);
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const { data, isLoading, refetch } = useNotificationsList({
    page,
    unread_only: unreadOnly,
  });
  const markRead = useMarkNotificationRead();
  const markAll = useMarkAllNotificationsRead();
  const push = usePushNotifications(VAPID_KEY);

  function openRow(href: string | null, id: string, isRead: boolean) {
    if (!isRead) markRead.mutate(id);
    if (href) navigate({ to: href });
  }

  const hasAlerts = (data?.items.length ?? 0) > 0;

  return (
    <PageContainer className="space-y-4">
      <PageHeader
        title="Alerts"
        actions={
          <>
            {hasAlerts && (
              <Button
                type="button"
                variant={unreadOnly ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  setUnreadOnly((v) => !v);
                  setPage(1);
                }}
              >
                Unread
              </Button>
            )}
            {hasAlerts && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => markAll.mutate()}
              >
                Mark all read
              </Button>
            )}
            {VAPID_KEY ? (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => void push.subscribe()}
              >
                Push alerts
              </Button>
            ) : null}
          </>
        }
      />

      <ul className="divide-y divide-border rounded-lg border border-border bg-card">
        {isLoading ? (
          <li className="px-4 py-8 text-center text-sm text-muted-foreground">
            Loading…
          </li>
        ) : null}
        {!isLoading && !hasAlerts ? (
          <li className="px-4 py-8">
            <EmptyState icon={Bell} heading="No alerts" size="sm" />
          </li>
        ) : null}
        {data?.items.map((row) => {
          const Icon = notificationIconFor(row.type);
          return (
            <li key={row.id}>
              <button
                type="button"
                className={cn(
                  "flex w-full gap-3 px-4 py-3 text-left hover:bg-secondary/50",
                  !row.is_read && "bg-primary/5",
                )}
                onClick={() => openRow(row.href, row.id, row.is_read)}
              >
                <span className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <Icon className="size-4" aria-hidden />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex items-start justify-between gap-2">
                    <span className="font-medium">{row.title}</span>
                    <span className="text-xs text-muted-foreground tabular-nums">
                      {formatRelativeTime(row.created_at)}
                    </span>
                  </span>
                  {row.body ? (
                    <span className="mt-0.5 text-sm text-muted-foreground">
                      {row.body}
                    </span>
                  ) : null}
                </span>
              </button>
            </li>
          );
        })}
      </ul>

      {data && data.total > data.page_size ? (
        <div className="flex justify-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={page * data.page_size >= data.total}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      ) : null}

      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => void refetch()}
      >
        <RefreshCw className="size-4" />
        Refresh
      </Button>
    </PageContainer>
  );
}
