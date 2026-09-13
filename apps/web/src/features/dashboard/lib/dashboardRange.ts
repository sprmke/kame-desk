import { todayIsoManila } from "@/lib/isoDate";

const MANILA_OFFSET = "+08:00";

export function addDaysIso(isoDate: string, days: number): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  const utc = new Date(Date.UTC(year, month - 1, day + days));
  const y = utc.getUTCFullYear();
  const m = String(utc.getUTCMonth() + 1).padStart(2, "0");
  const d = String(utc.getUTCDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function lastIsoDayOfMonth(isoDate: string): string {
  const [year, month] = isoDate.split("-").map(Number);
  const last = new Date(Date.UTC(year, month, 0)).getUTCDate();
  return `${year}-${String(month).padStart(2, "0")}-${String(last).padStart(2, "0")}`;
}

export function firstIsoDayOfMonth(isoDate: string): string {
  const [year, month] = isoDate.split("-").map(Number);
  return `${year}-${String(month).padStart(2, "0")}-01`;
}

export function manilaDateFromTimestamp(iso: string): string {
  return new Date(iso).toLocaleDateString("en-CA", { timeZone: "Asia/Manila" });
}

export function manilaRange(fromDate: string, toDate: string) {
  return {
    from_date: fromDate,
    to_date: toDate,
    start_from: `${fromDate}T00:00:00${MANILA_OFFSET}`,
    start_to: `${toDate}T23:59:59.999${MANILA_OFFSET}`,
  };
}

/** Current Manila month through the next 6 days (covers calendar dots + upcoming). */
export function dashboardAppointmentWindow(today = todayIsoManila()) {
  const monthStart = firstIsoDayOfMonth(today);
  const monthEnd = lastIsoDayOfMonth(today);
  const weekEnd = addDaysIso(today, 6);
  const toDate = weekEnd > monthEnd ? weekEnd : monthEnd;
  return { today, ...manilaRange(monthStart, toDate) };
}

export function formatManilaTime(iso: string) {
  return new Date(iso).toLocaleTimeString("en-PH", {
    timeZone: "Asia/Manila",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function formatManilaDayLabel(
  isoDate: string,
  today = todayIsoManila(),
) {
  if (isoDate === today) return "Today";
  if (isoDate === addDaysIso(today, 1)) return "Tomorrow";
  const [year, month, day] = isoDate.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day)).toLocaleDateString("en-PH", {
    timeZone: "UTC",
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

export function formatPhp(amount: string | number | null | undefined) {
  if (amount == null || amount === "") return "PHP 0.00";
  return `PHP ${amount}`;
}
