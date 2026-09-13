import { useEffect } from "react";
import { LIST_PAGE_SIZES, normalizeListPageLimit } from "@/lib/list/pagination";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useListToolbarMenuOpen } from "@/components/list/ListToolbarScope";

export function ListPerPageSelect({
  limit,
  onChange,
}: {
  limit: number;
  onChange: (limit: number) => void;
}) {
  const pageSize = normalizeListPageLimit(limit);
  const [open, setOpen] = useListToolbarMenuOpen();

  useEffect(() => {
    if (limit !== pageSize) onChange(pageSize);
  }, [limit, onChange, pageSize]);

  return (
    <Select
      value={String(pageSize)}
      open={open}
      onOpenChange={setOpen}
      onValueChange={(value) => onChange(Number(value))}
    >
      <SelectTrigger
        aria-label="Items per page"
        className="h-10 min-h-[44px] w-auto min-w-[3.5rem] gap-1 px-2.5 text-[13px] font-semibold shadow-theme-xs lg:min-h-10"
      >
        <SelectValue className="tabular-nums" />
      </SelectTrigger>
      <SelectContent align="end" className="min-w-[4.5rem]">
        {LIST_PAGE_SIZES.map((n) => (
          <SelectItem
            key={n}
            value={String(n)}
            className="text-[13px] font-semibold"
          >
            {n}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
