import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function SettingsSection({
  title,
  action,
  children,
  className,
  divided = true,
}: {
  title?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  divided?: boolean;
}) {
  return (
    <section className={cn("mb-8", className)}>
      {title || action ? (
        <div className="mb-2 flex items-center justify-between gap-3">
          {title ? (
            <h2 className="text-sm font-semibold text-foreground">{title}</h2>
          ) : (
            <span />
          )}
          {action}
        </div>
      ) : null}
      <div className={cn(divided && "divide-y divide-border")}>{children}</div>
    </section>
  );
}

export function SettingsRow({
  label,
  description,
  children,
  className,
}: {
  label: string;
  description?: string;
  children?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex min-h-12 flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-6",
        className,
      )}
    >
      <div className="min-w-0">
        <p className="text-sm font-medium text-foreground">{label}</p>
        {description ? (
          <p className="text-xs text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {children ? (
        <div className="shrink-0 sm:max-w-xs sm:text-right">{children}</div>
      ) : null}
    </div>
  );
}
