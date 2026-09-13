import {
  LIST_DEFAULT_PAGE_SIZE,
  normalizeListPageLimit,
} from "@/lib/list/pagination";
import { parseListView, type ListViewMode } from "@/lib/list/viewMode";

export type ListSearchBase = {
  q?: string;
  page?: number;
  limit?: number;
  sort?: string;
  view?: ListViewMode;
};

function positiveInt(value: unknown): number | undefined {
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n) || n < 1) return undefined;
  return Math.floor(n);
}

export function parseListSearchBase(
  search: Record<string, unknown>,
  views: readonly ListViewMode[],
): ListSearchBase {
  const q = typeof search.q === "string" && search.q ? search.q : undefined;
  const page = positiveInt(search.page);
  const limitRaw = positiveInt(search.limit);
  const limit = limitRaw != null ? normalizeListPageLimit(limitRaw) : undefined;
  const sort =
    typeof search.sort === "string" && search.sort ? search.sort : undefined;
  const view = parseListView(search.view, views, views[0] ?? "table");
  return {
    q,
    page: page && page > 1 ? page : undefined,
    limit: limit && limit !== LIST_DEFAULT_PAGE_SIZE ? limit : undefined,
    sort,
    view: view === (views[0] ?? "table") ? undefined : view,
  };
}

export function stringParam(value: unknown): string | undefined {
  return typeof value === "string" && value && value !== "all"
    ? value
    : undefined;
}
