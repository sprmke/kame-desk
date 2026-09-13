import { useCallback, useEffect, useMemo } from "react";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { useIsBelowLg } from "@/hooks/useMediaQuery";
import {
  LIST_DEFAULT_PAGE_SIZE,
  normalizeListPageLimit,
} from "@/lib/list/pagination";
import { parseListView, type ListViewMode } from "@/lib/list/viewMode";

type Options = {
  defaultSort: string;
  views: readonly ListViewMode[];
  extraKeys?: readonly string[];
};

const EMPTY_KEYS: readonly string[] = [];

function readString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function readPositiveInt(value: unknown, fallback: number): number {
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n) || n < 1) return fallback;
  return Math.floor(n);
}

export function useListSearch({
  defaultSort,
  views,
  extraKeys = EMPTY_KEYS,
}: Options) {
  const raw = useSearch({ strict: false }) as Record<string, unknown>;
  const navigate = useNavigate();
  const isBelowLg = useIsBelowLg();
  const desktopDefault: ListViewMode = views.includes("table")
    ? "table"
    : views[0]!;
  const mobileDefault: ListViewMode = views.includes("list")
    ? "list"
    : views.includes("grid")
      ? "grid"
      : views[0]!;

  const q = readString(raw.q);
  const page = readPositiveInt(raw.page, 1);
  const limit = normalizeListPageLimit(
    readPositiveInt(raw.limit, LIST_DEFAULT_PAGE_SIZE),
  );
  const sort = readString(raw.sort) || defaultSort;
  const requestedView = parseListView(
    raw.view,
    views,
    isBelowLg ? mobileDefault : desktopDefault,
  );
  const view: ListViewMode =
    isBelowLg && requestedView === "table" && views.includes("list")
      ? "list"
      : requestedView;

  const extrasSerialized = extraKeys
    .map((key) => `${key}\0${readString(raw[key])}`)
    .join("\n");
  const extras = useMemo(() => {
    const next: Record<string, string> = {};
    if (!extrasSerialized) return next;
    for (const part of extrasSerialized.split("\n")) {
      const sep = part.indexOf("\0");
      if (sep === -1) continue;
      next[part.slice(0, sep)] = part.slice(sep + 1);
    }
    return next;
  }, [extrasSerialized]);

  const setParams = useCallback(
    (patch: Record<string, string | number | undefined>) => {
      void navigate({
        // Cross-route list filters; per-route search schemas do not share a union.
        search: ((prev: Record<string, unknown>) => {
          const next: Record<string, unknown> = { ...prev, ...patch };
          const strip = (key: string, isDefault: boolean) => {
            if (isDefault || next[key] === "" || next[key] == null) {
              delete next[key];
            }
          };
          strip("q", next.q === "");
          strip("page", next.page === 1 || next.page === "1");
          strip("limit", Number(next.limit) === LIST_DEFAULT_PAGE_SIZE);
          strip("sort", next.sort === defaultSort);
          const defaultView = isBelowLg ? mobileDefault : desktopDefault;
          strip("view", next.view === defaultView);
          for (const key of extraKeys) {
            const value = next[key];
            if (value === "" || value === "all" || value == null)
              delete next[key];
          }
          return next;
        }) as never,
        replace: true,
      });
    },
    [
      defaultSort,
      desktopDefault,
      extraKeys,
      isBelowLg,
      mobileDefault,
      navigate,
    ],
  );

  useEffect(() => {
    if (!isBelowLg) return;
    if (requestedView === "table" && views.includes("list")) {
      setParams({ view: "list" });
    }
  }, [isBelowLg, requestedView, setParams, views]);

  const setPage = useCallback(
    (next: number) => setParams({ page: next }),
    [setParams],
  );
  const setLimit = useCallback(
    (next: number) => setParams({ limit: next, page: 1 }),
    [setParams],
  );
  const setSort = useCallback(
    (next: string) => setParams({ sort: next, page: 1 }),
    [setParams],
  );
  const setView = useCallback(
    (next: ListViewMode) => setParams({ view: next }),
    [setParams],
  );
  const setQuery = useCallback(
    (next: string) => setParams({ q: next, page: 1 }),
    [setParams],
  );

  return {
    q,
    page,
    limit,
    sort,
    view,
    extras,
    setParams,
    setPage,
    setLimit,
    setSort,
    setView,
    setQuery,
    isBelowLg,
    hideTableView: isBelowLg,
  };
}
