import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type Props = {
  label: string;
  value: ReactNode;
  icon: LucideIcon;
  hint?: string;
  tone?: "brand" | "success" | "warning" | "info";
  className?: string;
};

const toneClasses: Record<NonNullable<Props["tone"]>, string> = {
  brand:
    "bg-brand-50 text-brand-600 dark:bg-accent dark:text-accent-foreground",
  success:
    "bg-success-50 text-success-600 dark:bg-success/15 dark:text-success",
  warning:
    "bg-warning-50 text-warning-600 dark:bg-warning/15 dark:text-warning",
  info: "bg-info-50 text-info-600 dark:bg-info-500/15 dark:text-info-500",
};

export function StatCard({
  label,
  value,
  icon: Icon,
  hint,
  tone = "brand",
  className,
}: Props) {
  return (
    <Card className={cn("h-full", className)}>
      <CardContent className="flex items-start justify-between gap-3 py-5">
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="mt-1.5 text-2xl font-semibold text-foreground">
            {value}
          </p>
          {hint ? (
            <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
          ) : null}
        </div>
        <span
          className={cn(
            "flex size-10 shrink-0 items-center justify-center rounded-xl",
            toneClasses[tone],
          )}
        >
          <Icon className="size-5" />
        </span>
      </CardContent>
    </Card>
  );
}
