export const LIST_VIEW_MODES = ["table", "list", "grid", "calendar"] as const;

export type ListViewMode = (typeof LIST_VIEW_MODES)[number];

export function parseListView(
  value: unknown,
  allowed: readonly ListViewMode[],
  fallback: ListViewMode,
): ListViewMode {
  if (
    typeof value === "string" &&
    (allowed as readonly string[]).includes(value)
  ) {
    return value as ListViewMode;
  }
  return fallback;
}
