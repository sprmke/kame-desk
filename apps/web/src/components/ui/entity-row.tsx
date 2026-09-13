import { cn } from "@/lib/utils";

type EntityRowProps = {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  meta?: React.ReactNode;
  trailing?: React.ReactNode;
  className?: string;
};

export function EntityRow({
  title,
  subtitle,
  meta,
  trailing,
  className,
}: EntityRowProps) {
  return (
    <div
      data-slot="entity-row"
      className={cn(
        "flex min-h-11 items-center justify-between gap-3 py-3",
        className,
      )}
    >
      <div className="min-w-0">
        <p className="truncate font-medium text-foreground">{title}</p>
        {subtitle ? (
          <p className="mt-0.5 truncate text-sm text-muted-foreground">
            {subtitle}
          </p>
        ) : null}
        {meta ? (
          <p className="mt-0.5 truncate text-xs text-muted-foreground">
            {meta}
          </p>
        ) : null}
      </div>
      {trailing ? <div className="shrink-0">{trailing}</div> : null}
    </div>
  );
}

export function EntityList({
  className,
  ...props
}: React.ComponentProps<"ul">) {
  return (
    <ul
      data-slot="entity-list"
      className={cn("flex flex-col divide-y divide-border", className)}
      {...props}
    />
  );
}
