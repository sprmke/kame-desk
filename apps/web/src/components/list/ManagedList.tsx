import { useState, type ReactNode } from "react";
import type { ListViewMode } from "@/lib/list/viewMode";
import { listRange } from "@/lib/list/pagination";
import { ErrorState } from "@/components/ErrorState";
import {
  ListDesktopToolbar,
  ListMobileToolbar,
} from "@/components/list/ListDesktopToolbar";
import { ListPagination } from "@/components/list/ListPagination";
import { ListPerPageSelect } from "@/components/list/ListPerPageSelect";
import {
  ListRefinePopover,
  ListRefineSheet,
  ListTableShell,
} from "@/components/list/ListSurfaces";
import { ListSearchField } from "@/components/list/ListSearchField";
import {
  ListSortMenu,
  type ListSortOption,
} from "@/components/list/ListSortMenu";
import { ListSummary } from "@/components/list/ListSummary";
import { ListViewMenu } from "@/components/list/ListViewMenu";

export function ManagedList({
  entityLabel,
  total,
  page,
  limit,
  view,
  views,
  onViewChange,
  onPageChange,
  onLimitChange,
  sort,
  sortOptions,
  onSortChange,
  searchPlaceholder,
  searchValue,
  onSearchChange,
  leading,
  refine,
  refineCount = 0,
  onClearFilters,
  isLoading,
  isFetching,
  isError,
  onRetry,
  empty,
  hidePagination,
  hideTableView,
  children,
}: {
  entityLabel: string;
  total: number;
  page: number;
  limit: number;
  view: ListViewMode;
  views: readonly ListViewMode[];
  onViewChange: (view: ListViewMode) => void;
  onPageChange: (page: number) => void;
  onLimitChange: (limit: number) => void;
  sort?: string;
  sortOptions?: readonly ListSortOption[];
  onSortChange?: (sort: string) => void;
  searchPlaceholder?: string;
  searchValue: string;
  onSearchChange: (q: string) => void;
  leading?: ReactNode;
  refine?: ReactNode;
  refineCount?: number;
  onClearFilters?: () => void;
  isLoading?: boolean;
  isFetching?: boolean;
  isError?: boolean;
  onRetry?: () => void;
  empty?: ReactNode;
  hidePagination?: boolean;
  hideTableView?: boolean;
  children: ReactNode;
}) {
  const [desktopRefineOpen, setDesktopRefineOpen] = useState(false);
  const [mobileRefineOpen, setMobileRefineOpen] = useState(false);
  const { startIdx, endIdx, pageCount } = listRange(page, limit, total);
  const compact = total <= limit && pageCount <= 1;
  const showView = views.length > 1;
  const showPerPage = !compact || total > 12;
  const showPagination = !hidePagination && pageCount > 1;
  const search = (
    <ListSearchField
      value={searchValue}
      onChange={onSearchChange}
      placeholder={searchPlaceholder}
    />
  );
  const sortControl =
    sort && sortOptions && onSortChange ? (
      <ListSortMenu
        value={sort}
        onChange={onSortChange}
        options={sortOptions}
      />
    ) : null;
  const perPage = showPerPage ? (
    <ListPerPageSelect limit={limit} onChange={onLimitChange} />
  ) : null;
  const viewControl = showView ? (
    <ListViewMenu
      value={view}
      onChange={onViewChange}
      views={views}
      hideValues={hideTableView ? ["table"] : []}
    />
  ) : null;
  const desktopRefine = refine ? (
    <ListRefinePopover
      open={desktopRefineOpen}
      onOpenChange={setDesktopRefineOpen}
      activeCount={refineCount}
      onClear={onClearFilters}
    >
      {refine}
    </ListRefinePopover>
  ) : null;
  const mobileFilters =
    leading || refine ? (
      <ListRefineSheet
        open={mobileRefineOpen}
        onOpenChange={setMobileRefineOpen}
        activeCount={refineCount}
        onClear={onClearFilters}
      >
        {leading}
        {refine}
      </ListRefineSheet>
    ) : null;

  const showEmpty = !isLoading && !isError && total === 0 && Boolean(empty);
  const hideSummary = showEmpty || Boolean(isError);

  return (
    <div className="flex flex-col gap-3">
      <ListDesktopToolbar
        search={search}
        leading={leading}
        refine={desktopRefine}
        sort={sortControl}
        perPage={perPage}
        view={viewControl}
      />
      <ListMobileToolbar
        search={search}
        filters={mobileFilters}
        view={viewControl}
      />
      {!hideSummary ? (
        <div className="flex flex-wrap items-center justify-between gap-2 px-0.5">
          <ListSummary
            total={total}
            startIdx={startIdx}
            endIdx={endIdx}
            entityLabel={entityLabel}
            isLoading={isLoading}
            isFetching={isFetching}
          />
          <div className="flex items-center gap-2 lg:hidden">
            {sortControl}
            {perPage}
          </div>
        </div>
      ) : null}
      {isError ? (
        <ListTableShell>
          <ErrorState onRetry={onRetry} />
        </ListTableShell>
      ) : showEmpty ? (
        <ListTableShell>{empty}</ListTableShell>
      ) : (
        children
      )}
      {showPagination ? (
        <ListPagination
          page={page}
          pageCount={pageCount}
          isLoading={isLoading}
          onPageChange={onPageChange}
          ariaLabel={`${entityLabel} pages`}
        />
      ) : null}
    </div>
  );
}
