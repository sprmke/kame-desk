import { cn } from "@/lib/utils";

export const APPOINTMENT_STATUS_SHAPE = {
  Scheduled: "outline",
  Confirmed: "filled",
  Arrived: "square",
  "In Consultation": "diamond",
  Completed: "check",
  Cancelled: "slash",
  "No Show": "slash",
  Rescheduled: "outline",
} as const;

export const APPOINTMENT_STATUS_CLASS = {
  Scheduled: "text-[color:var(--status-scheduled)]",
  Confirmed: "text-[color:var(--status-confirmed)]",
  Arrived: "text-[color:var(--status-arrived)]",
  "In Consultation": "text-[color:var(--status-consult)]",
  Completed: "text-[color:var(--status-completed)]",
  Cancelled: "text-[color:var(--status-cancelled)]",
  "No Show": "text-[color:var(--status-noshow)]",
  Rescheduled: "text-[color:var(--status-rescheduled)]",
} as const;

type StatusLabel = keyof typeof APPOINTMENT_STATUS_SHAPE;

function Shape({
  kind,
}: {
  kind: (typeof APPOINTMENT_STATUS_SHAPE)[StatusLabel];
}) {
  const box = "size-2.5 shrink-0";
  if (kind === "filled") {
    return <span className={cn(box, "rounded-full bg-current")} />;
  }
  if (kind === "outline") {
    return <span className={cn(box, "rounded-full border-2 border-current")} />;
  }
  if (kind === "square") {
    return <span className={cn(box, "rounded-[2px] bg-current")} />;
  }
  if (kind === "diamond") {
    return <span className={cn(box, "rotate-45 rounded-[1px] bg-current")} />;
  }
  if (kind === "check") {
    return (
      <span
        className={cn(
          box,
          "flex items-center justify-center rounded-full border-2 border-current text-[8px] leading-none",
        )}
      >
        ✓
      </span>
    );
  }
  return (
    <span className={cn(box, "relative rounded-full border-2 border-current")}>
      <span className="absolute inset-x-0 top-1/2 h-px -translate-y-1/2 rotate-45 bg-current" />
    </span>
  );
}

export function StatusIndicator({
  status,
  className,
}: {
  status: string;
  className?: string;
}) {
  const key = status as StatusLabel;
  const shape = APPOINTMENT_STATUS_SHAPE[key] ?? "outline";
  const color = APPOINTMENT_STATUS_CLASS[key] ?? "text-muted-foreground";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-xs font-medium",
        color,
        className,
      )}
      aria-label={`Status: ${status}`}
      role={status === "No Show" || status === "Arrived" ? "status" : undefined}
    >
      <Shape kind={shape} />
      <span>{status}</span>
    </span>
  );
}

export const CALENDAR_STATUS_COLOR: Record<string, string> = {
  Scheduled: "var(--status-scheduled)",
  Confirmed: "var(--status-confirmed)",
  Cancelled: "var(--status-cancelled)",
  "No Show": "var(--status-noshow)",
  Rescheduled: "var(--status-rescheduled)",
};

export const DOCTOR_CAT_COLORS = [
  "var(--cat-1)",
  "var(--cat-2)",
  "var(--cat-3)",
  "var(--cat-4)",
] as const;

const PAYMENT_STATUS_SHAPE = {
  draft: "outline",
  issued: "filled",
  paid: "check",
  partial: "diamond",
  partially_paid: "diamond",
  overdue: "slash",
  void: "slash",
} as const;

const PAYMENT_STATUS_CLASS = {
  draft: "text-muted-foreground",
  issued: "text-[color:var(--status-confirmed)]",
  paid: "text-[color:var(--status-completed)]",
  partial: "text-[color:var(--status-arrived)]",
  partially_paid: "text-[color:var(--status-arrived)]",
  overdue: "text-[color:var(--status-noshow)]",
  void: "text-muted-foreground",
} as const;

export function PaymentStatus({
  status,
  className,
}: {
  status: string;
  className?: string;
}) {
  const key = status as keyof typeof PAYMENT_STATUS_SHAPE;
  const shape = PAYMENT_STATUS_SHAPE[key] ?? "outline";
  const color = PAYMENT_STATUS_CLASS[key] ?? "text-muted-foreground";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-xs font-medium capitalize",
        color,
        className,
      )}
      aria-label={`Payment status: ${status.replaceAll("_", " ")}`}
    >
      <Shape kind={shape} />
      <span>{status.replaceAll("_", " ")}</span>
    </span>
  );
}
