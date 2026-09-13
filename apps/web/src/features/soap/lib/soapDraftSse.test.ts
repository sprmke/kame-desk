import { describe, expect, it } from "vitest";
import { applySoapDraftField, parseSseChunk } from "./soapDraftSse";

describe("parseSseChunk", () => {
  it("parses field and done events", () => {
    const chunk =
      'data: {"type":"field","field":"subjective","value":"Cough"}\n\n' +
      'data: {"type":"done"}\n\n';
    const { events, remainder } = parseSseChunk(chunk);
    expect(events).toEqual([
      { type: "field", field: "subjective", value: "Cough" },
      { type: "done" },
    ]);
    expect(remainder).toBe("");
  });

  it("keeps partial trailing data in remainder", () => {
    const chunk = 'data: {"type":"field","field":"plan","value":"Rest';
    const { events, remainder } = parseSseChunk(chunk);
    expect(events).toEqual([]);
    expect(remainder).toBe(chunk);
  });
});

describe("applySoapDraftField", () => {
  it("merges streamed field values", () => {
    const next = applySoapDraftField({ subjective: "A" }, "plan", "Rest");
    expect(next).toEqual({ subjective: "A", plan: "Rest" });
  });
});
