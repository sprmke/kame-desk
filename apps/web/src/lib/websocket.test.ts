import { describe, expect, it } from "vitest";
import { nextBackoffMs, shouldUsePolling } from "./websocket";

describe("websocket helpers", () => {
  it("exponential backoff caps at max", () => {
    expect(nextBackoffMs(0)).toBe(1000);
    expect(nextBackoffMs(3)).toBe(8000);
    expect(nextBackoffMs(10)).toBe(30000);
  });

  it("switches to polling after repeated failures", () => {
    expect(shouldUsePolling("connected", 0)).toBe(false);
    expect(shouldUsePolling("connecting", 2)).toBe(true);
    expect(shouldUsePolling("polling", 0)).toBe(true);
  });
});
