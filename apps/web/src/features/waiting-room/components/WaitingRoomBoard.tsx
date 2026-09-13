import {
  columnForItem,
  formatTime,
  nextVisitStatus,
  type WaitingRoomItem,
} from "../lib/waitingRoom";
import {
  computeWaitStats,
  sortArrivedByLongestWait,
  type WaitUrgency,
} from "../lib/waitTime";
import { VisitSummaryPanel } from "@/features/visit-summary/components/VisitSummaryPanel";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  SwipeRevealRow,
  type SwipeRevealAction,
} from "@/components/mobile/SwipeRevealRow";
import { InitialsAvatar } from "@/components/PersonIdentity";
import { cn } from "@/lib/utils";

type Props = {
  item: WaitingRoomItem;
  onAdvance: (
    id: string,
    status: "Arrived" | "In Consultation" | "Completed",
  ) => void;
  pendingId: string | null;
  swipeActions?: boolean;
  now?: Date;
};

const URGENCY_BADGE: Record<WaitUrgency, "success" | "warning" | "outline"> = {
  normal: "success",
  delayed: "outline",
  overdue: "warning",
};

export function WaitingRoomCard({
  item,
  onAdvance,
  pendingId,
  swipeActions,
  now,
}: Props) {
  const next = nextVisitStatus(item.current_visit_status);
  const busy = pendingId === item.id;
  const showWait =
    item.current_visit_status === "Arrived" ||
    item.current_visit_status === "In Consultation";
  const waitStats = showWait
    ? computeWaitStats(item.scheduled_start, now ?? new Date())
    : null;

  const actions: SwipeRevealAction[] = next
    ? [
        {
          key: "advance",
          label: next,
          variant: "default",
          onClick: () => onAdvance(item.id, next),
        },
      ]
    : [];

  const body = (
    <Card className={cn("p-3 native-press", swipeActions && "shadow-none")}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2 font-medium text-foreground">
          <InitialsAvatar
            name={item.patient_name ?? "Patient"}
            className="size-7 text-[10px]"
          />
          <span className="truncate">{item.patient_name ?? "Patient"}</span>
        </div>
        {waitStats ? (
          <Badge
            variant={URGENCY_BADGE[waitStats.urgency]}
            className="shrink-0 tabular-nums"
            aria-label={waitStats.formatted}
          >
            {waitStats.formatted}
          </Badge>
        ) : null}
      </div>
      <div className="mt-0.5 text-xs text-muted-foreground">
        {formatTime(item.scheduled_start)} · {item.doctor_name ?? "Doctor"}
      </div>
      {item.reason_for_visit && (
        <div className="mt-1 text-xs text-muted-foreground">
          {item.reason_for_visit}
        </div>
      )}
      {next ? (
        <Button
          type="button"
          size="sm"
          disabled={busy}
          className="mt-3 w-full"
          onClick={() => onAdvance(item.id, next)}
        >
          {busy ? "Updating…" : next}
        </Button>
      ) : null}
      {item.current_visit_status === "Completed" && (
        <VisitSummaryPanel appointmentId={item.id} />
      )}
    </Card>
  );

  if (swipeActions && next) {
    return (
      <SwipeRevealRow actions={actions} disabled={busy}>
        {body}
      </SwipeRevealRow>
    );
  }

  return body;
}

export function WaitingRoomColumn({
  title,
  items,
  onAdvance,
  pendingId,
  swipeActions,
  now,
}: {
  title: string;
  items: WaitingRoomItem[];
  onAdvance: Props["onAdvance"];
  pendingId: string | null;
  swipeActions?: boolean;
  now?: Date;
}) {
  const ordered =
    title === "Arrived"
      ? sortArrivedByLongestWait(items, now ?? new Date())
      : items;

  return (
    <section className="flex min-w-0 flex-1 flex-col gap-2.5 rounded-2xl border border-border bg-secondary/30 p-3 lg:min-w-[240px]">
      <header className="flex items-center justify-between px-1 text-sm font-medium text-foreground">
        <span>{title}</span>
        <Badge variant="outline" className="rounded-md tabular-nums" dot>
          {items.length}
        </Badge>
      </header>
      <div className="flex flex-col gap-2">
        {ordered.length === 0 ? (
          <p className="py-8 text-center text-xs text-muted-foreground">
            Empty
          </p>
        ) : (
          ordered.map((item) => (
            <WaitingRoomCard
              key={item.id}
              item={item}
              onAdvance={onAdvance}
              pendingId={pendingId}
              swipeActions={swipeActions}
              now={now}
            />
          ))
        )}
      </div>
    </section>
  );
}

export function filterActiveWaiting(items: WaitingRoomItem[]) {
  return items.filter((item) => columnForItem(item) !== "Completed");
}
