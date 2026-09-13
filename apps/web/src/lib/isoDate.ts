/** Local calendar date helpers. Values are `YYYY-MM-DD` (no timezone shift). */

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

export function parseIsoDate(value?: string | null): Date | undefined {
  if (!value || !ISO_DATE.test(value)) return undefined;
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(year, month - 1, day);
  if (
    date.getFullYear() !== year ||
    date.getMonth() !== month - 1 ||
    date.getDate() !== day
  ) {
    return undefined;
  }
  return date;
}

export function toIsoDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/** Today's date in Asia/Manila as `YYYY-MM-DD`. */
export function todayIsoManila(): string {
  return new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Manila" });
}
