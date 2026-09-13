import * as React from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

function SearchInput({ className, ...props }: React.ComponentProps<"input">) {
  return (
    <div className="relative min-w-0 flex-1">
      <Search
        className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
        aria-hidden
      />
      <Input
        type="search"
        data-slot="search-input"
        className={cn("pl-9", className)}
        {...props}
      />
    </div>
  );
}

export { SearchInput };
