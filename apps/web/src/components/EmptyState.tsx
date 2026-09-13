import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type Props = {
  icon: LucideIcon;
  heading: string;
  description?: string;
  action?: React.ReactNode;
  size?: "default" | "sm";
  className?: string;
};

export function EmptyState({
  icon: Icon,
  heading,
  description,
  action,
  size = "default",
  className,
}: Props) {
  const compact = size === "sm";
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-2 px-4 text-center",
        compact ? "py-8" : "py-16",
        className,
      )}
    >
      <Icon
        className={cn("text-muted-foreground", compact ? "size-6" : "size-8")}
        aria-hidden
      />
      <p className="text-sm font-medium text-foreground">{heading}</p>
      {description ? (
        <p className="max-w-sm text-sm text-muted-foreground">{description}</p>
      ) : null}
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  );
}

/** Card chrome for section bodies (empty, error, or rows) that are not already in a list shell. */
export function SectionCard({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Card className={cn("w-full", className)}>
      <CardContent>{children}</CardContent>
    </Card>
  );
}
