import type { KeyboardEvent, ReactNode } from "react";
import { ChevronDown, SlidersHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useClaimToolbarMenu } from "@/components/list/ListToolbarScope";
import { listControlClass } from "@/components/list/listControlClass";

function FilterCount({ count }: { count: number }) {
  if (count <= 0) return null;
  return (
    <span className="inline-flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold tabular-nums text-primary-foreground">
      {count > 9 ? "9+" : count}
    </span>
  );
}

export function ListRefinePopover({
  open,
  onOpenChange,
  activeCount = 0,
  onClear,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  activeCount?: number;
  onClear?: () => void;
  children: ReactNode;
}) {
  const menu = useClaimToolbarMenu(open, onOpenChange);
  const active = activeCount > 0 || menu.open;

  return (
    <Popover open={menu.open} onOpenChange={menu.onOpenChange}>
      <PopoverTrigger asChild>
        <button
          type="button"
          aria-label="Filters"
          aria-expanded={menu.open}
          aria-haspopup="dialog"
          className={cn(
            listControlClass,
            active && "border-primary/30 bg-primary/10 text-primary",
          )}
        >
          <SlidersHorizontal className="size-3.5 shrink-0" aria-hidden />
          <span>Filters</span>
          <FilterCount count={activeCount} />
          <ChevronDown
            className={cn(
              "size-3.5 shrink-0 transition-transform duration-150",
              menu.open && "rotate-180",
            )}
            aria-hidden
          />
        </button>
      </PopoverTrigger>
      <PopoverContent
        align="end"
        className="w-[min(calc(100vw-2rem),16rem)] p-0"
      >
        {onClear && activeCount > 0 ? (
          <div className="flex items-center justify-end border-b border-border px-2.5 py-1.5">
            <button
              type="button"
              onClick={onClear}
              className="text-xs font-semibold text-muted-foreground hover:text-foreground"
            >
              Clear
            </button>
          </div>
        ) : null}
        <div className="flex flex-col gap-3 p-3">{children}</div>
      </PopoverContent>
    </Popover>
  );
}

export function ListRefineSheet({
  open,
  onOpenChange,
  activeCount = 0,
  onClear,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  activeCount?: number;
  onClear?: () => void;
  children: ReactNode;
}) {
  return (
    <>
      <Button
        type="button"
        variant="outline"
        className="h-10 min-h-[44px] gap-1.5"
        aria-label="Filters"
        onClick={() => onOpenChange(true)}
      >
        <SlidersHorizontal className="size-3.5" aria-hidden />
        Filters
        <FilterCount count={activeCount} />
      </Button>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent side="bottom" className="gap-3 px-4 pb-6">
          <SheetHeader className="flex-row items-center justify-between space-y-0">
            <SheetTitle>Filters</SheetTitle>
            {onClear && activeCount > 0 ? (
              <button
                type="button"
                onClick={onClear}
                className="text-sm font-semibold text-muted-foreground hover:text-foreground"
              >
                Clear
              </button>
            ) : null}
          </SheetHeader>
          <div className="flex flex-col gap-3">{children}</div>
        </SheetContent>
      </Sheet>
    </>
  );
}

export function ListCardGrid({
  children,
  isFetching,
}: {
  children: ReactNode;
  isFetching?: boolean;
}) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 gap-2 sm:grid-cols-2 sm:gap-3.5 lg:grid-cols-3 lg:gap-4",
        "transition-opacity duration-300",
        isFetching && "opacity-60",
      )}
    >
      {children}
    </div>
  );
}

export function ListCardButton({
  children,
  onOpen,
  "aria-label": ariaLabel,
  className,
}: {
  children: ReactNode;
  onOpen?: () => void;
  "aria-label"?: string;
  className?: string;
}) {
  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (!onOpen) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onOpen();
    }
  };
  return (
    <div
      role={onOpen ? "button" : undefined}
      tabIndex={onOpen ? 0 : undefined}
      aria-label={ariaLabel}
      onClick={onOpen}
      onKeyDown={onOpen ? onKeyDown : undefined}
      className={cn(
        "flex min-h-[44px] flex-col rounded-2xl border border-border bg-card p-4 shadow-theme-xs",
        onOpen &&
          "cursor-pointer transition-[box-shadow,transform,border-color] duration-150 ease-theme hover:border-primary/20 hover:shadow-theme-sm motion-safe:active:scale-[0.99] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function ListStack({ children }: { children: ReactNode }) {
  return (
    <ul className="flex flex-col divide-y divide-border overflow-hidden rounded-2xl border border-border bg-card shadow-theme-xs">
      {children}
    </ul>
  );
}

export function ListTableShell({ children }: { children: ReactNode }) {
  return (
    <div className="w-full overflow-hidden rounded-2xl border border-border bg-card shadow-theme-xs">
      {children}
    </div>
  );
}
