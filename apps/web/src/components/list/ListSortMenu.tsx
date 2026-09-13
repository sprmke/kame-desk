import { Check, ChevronDown } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useListToolbarMenuOpen } from "@/components/list/ListToolbarScope";
import { listControlClass } from "@/components/list/listControlClass";

export type ListSortOption = { value: string; label: string };

export function ListSortHeader({
  label,
  column,
  sort,
  onSort,
}: {
  label: string;
  column: string;
  sort: string;
  onSort: (next: string) => void;
}) {
  const [key, dir] = sort.split(":");
  const active = key === column;
  const next = active && dir === "asc" ? `${column}:desc` : `${column}:asc`;
  return (
    <button
      type="button"
      className="inline-flex items-center gap-1 hover:text-foreground"
      onClick={() => onSort(next)}
    >
      {label}
      <span className="text-[10px] tabular-nums text-muted-foreground">
        {active ? (dir === "desc" ? "↓" : "↑") : ""}
      </span>
    </button>
  );
}

export function ListSortMenu({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (next: string) => void;
  options: readonly ListSortOption[];
}) {
  const [open, setOpen] = useListToolbarMenuOpen();
  const current =
    options.find((option) => option.value === value) ?? options[0];

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <button type="button" aria-label="Sort" className={listControlClass}>
          <span className="truncate">{current?.label ?? "Sort"}</span>
          <ChevronDown
            className="size-3.5 shrink-0 text-muted-foreground"
            aria-hidden
          />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-[11rem]">
        {options.map((option) => {
          const selected = option.value === value;
          return (
            <DropdownMenuItem
              key={option.value}
              onSelect={() => onChange(option.value)}
              className="gap-2"
              aria-checked={selected}
              role="menuitemradio"
            >
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
