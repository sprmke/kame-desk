export type RecurrencePreset = "weekly" | "biweekly" | "monthly";

export function rruleFromPreset(preset: RecurrencePreset, count = 12): string {
  switch (preset) {
    case "weekly":
      return `FREQ=WEEKLY;COUNT=${count}`;
    case "biweekly":
      return `FREQ=WEEKLY;INTERVAL=2;COUNT=${count}`;
    case "monthly":
      return `FREQ=MONTHLY;COUNT=${count}`;
    default:
      return `FREQ=WEEKLY;COUNT=${count}`;
  }
}
