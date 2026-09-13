import { useEffect, useState } from "react";
import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";

export function ListSearchField({
  value,
  onChange,
  placeholder = "Search",
  "aria-label": ariaLabel = "Search",
}: {
  value: string;
  onChange: (next: string) => void;
  placeholder?: string;
  "aria-label"?: string;
}) {
  const [draft, setDraft] = useState(value);

  useEffect(() => {
    setDraft(value);
  }, [value]);

  useEffect(() => {
    const t = window.setTimeout(() => {
      if (draft !== value) onChange(draft);
    }, 280);
    return () => window.clearTimeout(t);
  }, [draft, onChange, value]);

  return (
    <div className="relative min-w-0 flex-1">
      <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        placeholder={placeholder}
        aria-label={ariaLabel}
        className="h-10 min-h-[44px] pl-9 pr-9 lg:min-h-10"
      />
      {draft ? (
        <button
          type="button"
          aria-label="Clear search"
          className="absolute right-2 top-1/2 inline-flex size-7 -translate-y-1/2 items-center justify-center rounded-md text-muted-foreground hover:text-foreground"
          onClick={() => {
            setDraft("");
            onChange("");
          }}
        >
          <X className="size-3.5" />
        </button>
      ) : null}
    </div>
  );
}
