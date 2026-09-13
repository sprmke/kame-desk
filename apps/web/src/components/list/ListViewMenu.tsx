import {
  CalendarDays,
  Check,
  ChevronDown,
  LayoutGrid,
  List,
  Table2,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useIsBelowLg } from "@/hooks/useMediaQuery";
import type { ListViewMode } from "@/lib/list/viewMode";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useListToolbarMenuOpen } from "@/components/list/ListToolbarScope";
import { listControlClass } from "@/components/list/listControlClass";

const VIEW_META: Record<ListViewMode, { label: string; Icon: LucideIcon }> = {
  table: { label: "Table", Icon: Table2 },
  list: { label: "List", Icon: List },
  grid: { label: "Grid", Icon: LayoutGrid },
  calendar: { label: "Calendar", Icon: CalendarDays },
};

export function ListViewMenu({
  value,
  onChange,
  views,
  hideValues = [],
  ariaLabel = "Choose list view",
}: {
  value: ListViewMode;
  onChange: (next: ListViewMode) => void;
  views: readonly ListViewMode[];
  hideValues?: ListViewMode[];
  ariaLabel?: string;
}) {
  const [open, setOpen] = useListToolbarMenuOpen();
  const isMobileLayout = useIsBelowLg();
  const visible = views.filter((view) => !hideValues.includes(view));
  const current = visible.includes(value) ? value : visible[0];
  const meta = current ? VIEW_META[current] : VIEW_META.list;
  const CurrentIcon = meta.Icon;

  const trigger = (
    <button
      type="button"
      aria-label={ariaLabel}
      aria-expanded={open}
      aria-haspopup={isMobileLayout ? "dialog" : "menu"}
      onClick={isMobileLayout ? () => setOpen((next) => !next) : undefined}
      className={listControlClass}
    >
      <CurrentIcon className="size-3.5 shrink-0" aria-hidden />
      <span className="truncate">{meta.label}</span>
      <ChevronDown
        className={cn(
          "size-3.5 shrink-0 text-muted-foreground transition-transform duration-150",
          open && "rotate-180",
        )}
        aria-hidden
      />
    </button>
  );

  if (isMobileLayout) {
    return (
      <>
        {trigger}
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetContent side="bottom" className="gap-2 px-3 pb-6">
            <SheetHeader>
              <SheetTitle>{ariaLabel}</SheetTitle>
            </SheetHeader>
            <div
              role="listbox"
              aria-label={ariaLabel}
              className="flex flex-col gap-1"
            >
              {visible.map((optionValue) => {
                const option = VIEW_META[optionValue];
                const Icon = option.Icon;
                const selected = optionValue === value;
                return (
                  <button
                    key={optionValue}
                    type="button"
                    role="option"
                    aria-selected={selected}
                    className={cn(
                      "flex min-h-[44px] items-center gap-3 rounded-lg px-3 text-sm font-medium",
                      selected
                        ? "bg-primary/10 text-primary"
                        : "hover:bg-muted",
                    )}
                    onClick={() => {
                      onChange(optionValue);
                      setOpen(false);
                    }}
                  >
                    <Icon className="size-5" aria-hidden />
                    <span className="flex-1 text-left">{option.label}</span>
                    {selected ? <Check className="size-4" aria-hidden /> : null}
                  </button>
                );
              })}
            </div>
          </SheetContent>
        </Sheet>
      </>
    );
  }

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>{trigger}</DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-[10.5rem]">
        {visible.map((optionValue) => {
          const option = VIEW_META[optionValue];
          const Icon = option.Icon;
          const selected = optionValue === value;
          return (
            <DropdownMenuItem
              key={optionValue}
              onSelect={() => onChange(optionValue)}
              className="gap-2"
              aria-checked={selected}
              role="menuitemradio"
            >
              <Icon className="size-3.5 shrink-0" aria-hidden />
              <span className="flex-1">{option.label}</span>
              {selected ? (
                <Check className="size-3.5 shrink-0 text-primary" aria-hidden />
              ) : null}
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
