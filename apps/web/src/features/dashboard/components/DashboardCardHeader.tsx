import { Link } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { CardHeader } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type DashboardPath =
  | "/dashboard/appointments"
  | "/dashboard/appointments/calendar"
  | "/dashboard/waiting-room"
  | "/dashboard/billing/invoices"
  | "/dashboard/billing/claims"
  | "/dashboard/recalls"
  | "/dashboard/reminders"
  | "/dashboard/reports"
  | "/dashboard/patients";

export function DashboardCardHeader({
  title,
  to,
  extra,
}: {
  title: string;
  to?: DashboardPath;
  extra?: ReactNode;
}) {
  return (
    <CardHeader
      divided
      className="h-14 flex-row items-center justify-between gap-2 space-y-0 py-0"
    >
      <div className="flex min-w-0 items-center gap-2">
        <h2 className="truncate text-base font-semibold leading-none">
          {title}
        </h2>
        {extra}
      </div>
      {to ? (
        <Link
          to={to}
          className={cn(
            buttonVariants({ variant: "ghost", size: "sm" }),
            "min-h-11 shrink-0 px-3",
          )}
        >
          All
        </Link>
      ) : null}
    </CardHeader>
  );
}
