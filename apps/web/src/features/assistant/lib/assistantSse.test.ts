import { describe, expect, it } from "vitest";
import { parseAssistantSseChunk } from "./assistantSse";

describe("parseAssistantSseChunk", () => {
  it("parses text and confirm_card events", () => {
    const buffer =
      'data: {"type":"text","content":"Found 1 patients."}\n\n' +
      'data: {"type":"confirm_card","action_id":"a1","tool":"propose_cancel_appointment","tier":2,"proposal":{}}\n\n';
    const { events, remainder } = parseAssistantSseChunk(buffer);
    expect(events).toHaveLength(2);
    expect(events[0]).toMatchObject({ type: "text" });
    expect(events[1]).toMatchObject({ type: "confirm_card", action_id: "a1" });
    expect(remainder).toBe("");
  });
});
