import { cn } from "@/lib/utils";

export const listControlClass = cn(
  "inline-flex h-10 min-h-[44px] shrink-0 items-center gap-1.5 rounded-lg border border-border bg-card px-3 text-[13px] font-semibold text-foreground",
  "transition-colors duration-150 ease-theme hover:bg-muted/60",
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
  "lg:min-h-10",
);
