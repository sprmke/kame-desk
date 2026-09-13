/** Shared dashboard card chrome so sibling cards in a row stay even. */
export const dashboardCardClass = "flex h-full min-w-0 flex-col";

/** Today / Queue: five 44px rows, then scroll. Height never depends on item count. */
export const dashboardListBodyClass =
  "flex h-60 min-h-0 flex-col overflow-y-auto px-3 py-2 sm:px-3";

/** Follow-up modules: same body as Today / Queue. */
export const dashboardFollowUpBodyClass = dashboardListBodyClass;

/** Calendar + upcoming: shared week band. Calendar fills this, no spare padding. */
export const dashboardWeekBodyClass =
  "flex h-[22rem] min-h-0 flex-col overflow-hidden px-2 py-2 sm:px-3";

/** 14-day trend: same band as upcoming so the row stays even. */
export const dashboardChartBodyClass =
  "flex h-[22rem] min-h-0 flex-col overflow-hidden px-3 py-2 sm:px-4";
