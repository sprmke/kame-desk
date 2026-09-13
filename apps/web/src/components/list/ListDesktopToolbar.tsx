import type { ReactNode } from "react";
import { ListToolbarScope } from "@/components/list/ListToolbarScope";

export function ListDesktopToolbar({
  search,
  leading,
  refine,
  sort,
  perPage,
  view,
  "aria-label": ariaLabel = "List filters",
}: {
  search: ReactNode;
  leading?: ReactNode;
  refine?: ReactNode;
  sort?: ReactNode;
  perPage?: ReactNode;
  view?: ReactNode;
  "aria-label"?: string;
}) {
  const hasFilters = Boolean(leading || refine);
  const hasChrome = Boolean(sort || perPage || view);

  return (
    <ListToolbarScope>
      <div
        role="toolbar"
        aria-label={ariaLabel}
        aria-orientation="horizontal"
        className="hidden w-full min-w-0 items-center gap-3 lg:flex"
      >
        {hasFilters ? (
          <div
            role="group"
            aria-label="Filter by"
            className="flex shrink-0 items-center gap-2"
          >
            {leading}
            {refine}
          </div>
        ) : null}
        <div className="min-w-0 flex-1">{search}</div>
        {hasChrome ? (
          <div
            role="group"
            aria-label="Sort and view"
            className="flex shrink-0 items-center gap-2"
          >
            {sort}
            {perPage}
            {view}
          </div>
        ) : null}
      </div>
    </ListToolbarScope>
  );
}

export function ListMobileToolbar({
  search,
  filters,
  view,
}: {
  search: ReactNode;
  filters?: ReactNode;
  view?: ReactNode;
}) {
  return (
    <div className="flex w-full min-w-0 items-center gap-2 lg:hidden">
      <div className="min-w-0 flex-1">{search}</div>
      {filters}
      {view}
    </div>
  );
}
