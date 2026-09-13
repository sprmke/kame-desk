import { describe, expect, it } from "vitest";
import {
  DEFAULT_NOTIFICATION_PREFERENCES,
  isRecallStatus,
  mergeNotificationPreferences,
} from "./preferences";

describe("mergeNotificationPreferences", () => {
  it("fills defaults when prefs are empty", () => {
    expect(mergeNotificationPreferences(null)).toEqual(
      DEFAULT_NOTIFICATION_PREFERENCES,
    );
  });

  it("merges partial updates", () => {
    expect(
      mergeNotificationPreferences({ reminder_2h_enabled: true }),
    ).toMatchObject({
      reminder_2h_enabled: true,
      reminder_24h_enabled: true,
    });
  });
});

describe("isRecallStatus", () => {
  it("accepts valid recall statuses", () => {
    expect(isRecallStatus("pending")).toBe(true);
    expect(isRecallStatus("booked")).toBe(true);
  });

  it("rejects invalid values", () => {
    expect(isRecallStatus("open")).toBe(false);
  });
});
