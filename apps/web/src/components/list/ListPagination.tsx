import type { ReactNode } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { buildPageItems, type PageItem } from "@/lib/list/pagination";
import { cn } from "@/lib/utils";

function PaginationBtn({
  children,
  onClick,
  disabled,
  "aria-label": ariaLabel,
}: {
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
  "aria-label": string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      className={cn(
        "inline-flex min-h-[44px] min-w-[44px] items-center justify-center gap-1 rounded-lg px-3",
        "border border-border bg-card text-sm font-semibold text-muted-foreground",
        "transition-colors duration-150 ease-theme",
        "hover:bg-muted hover:text-foreground",
        "disabled:pointer-events-none disabled:opacity-40",
        "lg:min-h-8 lg:min-w-8 lg:px-3 lg:py-1.5",
      )}
    >
      {children}
    </button>
  );
}

export function ListPagination({
  page,
  pageCount,
  isLoading = false,
  onPageChange,
  ariaLabel,
}: {
  page: number;
  pageCount: number;
  isLoading?: boolean;
  onPageChange: (page: number) => void;
  ariaLabel: string;
}) {
  if (pageCount <= 1) return null;
  const pageItems: PageItem[] = buildPageItems(page, pageCount);
  return (
    <nav
      aria-label={ariaLabel}
      className="flex items-center justify-center gap-1 pt-2"
    >
      <PaginationBtn
        onClick={() => onPageChange(Math.max(1, page - 1))}
        disabled={page <= 1 || isLoading}
        aria-label="Previous page"
      >
        <ChevronLeft className="size-4" aria-hidden />
        <span className="hidden sm:inline">Prev</span>
      </PaginationBtn>
      <div className="flex max-w-[min(100%,240px)] items-center gap-0.5 overflow-x-auto px-0.5 sm:max-w-none">
        {pageItems.map((item, idx) =>
          item === "ellipsis" ? (
            <span
              key={`dots-${idx}`}
              className="flex size-10 shrink-0 select-none items-center justify-center text-sm text-muted-foreground lg:size-8"
            >
              …
            </span>
          ) : (
            <button
              key={item}
              type="button"
              onClick={() => onPageChange(item)}
              aria-label={`Go to page ${item}`}
              aria-current={item === page ? "page" : undefined}
              className={cn(
                "flex size-10 shrink-0 items-center justify-center rounded-lg text-sm font-semibold transition-colors duration-150 lg:size-8",
                item === page
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              {item}
            </button>
          ),
        )}
      </div>
      <PaginationBtn
        onClick={() => onPageChange(Math.min(pageCount, page + 1))}
        disabled={page >= pageCount || isLoading}
        aria-label="Next page"
      >
        <span className="hidden sm:inline">Next</span>
        <ChevronRight className="size-4" aria-hidden />
      </PaginationBtn>
    </nav>
  );
}
