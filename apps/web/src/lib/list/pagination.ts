export const LIST_PAGE_SIZES = [25, 50, 100] as const;

export const LIST_DEFAULT_PAGE_SIZE = LIST_PAGE_SIZES[0];

export type PageItem = number | "ellipsis";

export function normalizeListPageLimit(value: number): number {
  return (LIST_PAGE_SIZES as readonly number[]).includes(value)
    ? value
    : LIST_DEFAULT_PAGE_SIZE;
}

export function buildPageItems(current: number, total: number): PageItem[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);

  const items: PageItem[] = [1];
  if (current > 3) items.push("ellipsis");

  const lo = Math.max(2, current - 1);
  const hi = Math.min(total - 1, current + 1);
  for (let p = lo; p <= hi; p++) items.push(p);

  if (current < total - 2) items.push("ellipsis");
  items.push(total);
  return items;
}

export function listRange(page: number, limit: number, total: number) {
  if (total === 0) return { startIdx: 0, endIdx: 0, pageCount: 1 };
  const pageCount = Math.max(1, Math.ceil(total / limit));
  const safePage = Math.min(Math.max(1, page), pageCount);
  const startIdx = (safePage - 1) * limit + 1;
  const endIdx = Math.min(safePage * limit, total);
  return { startIdx, endIdx, pageCount };
}
