import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Props = {
  heading?: string;
  description?: string;
  onRetry?: () => void;
  className?: string;
};

export function ErrorState({
  heading = "Could not load",
  description,
  onRetry,
  className,
}: Props) {
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-center gap-2 px-4 py-16 text-center",
        className,
      )}
    >
      <AlertCircle className="size-8 text-destructive" aria-hidden />
      <p className="text-sm font-medium text-foreground">{heading}</p>
      {description ? (
        <p className="max-w-sm text-sm text-muted-foreground">{description}</p>
      ) : null}
      {onRetry ? (
        <Button type="button" variant="outline" size="sm" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}

export function InlineError({
  heading = "Could not load",
  onRetry,
  className,
}: Omit<Props, "description">) {
  return (
    <div
      role="alert"
      className={cn(
        "flex items-center justify-between gap-3 rounded-lg border border-destructive/30 bg-error-50 px-3 py-2 text-sm dark:bg-error-950/40",
        className,
      )}
    >
      <p className="text-foreground">{heading}</p>
      {onRetry ? (
        <Button type="button" variant="ghost" size="sm" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}
