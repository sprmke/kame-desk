import "fake-indexeddb/auto";
import { beforeEach, describe, expect, it } from "vitest";
import {
  enqueueSoapDraft,
  generateClientDraftToken,
  listQueuedSoapDrafts,
  removeQueuedSoapDraft,
} from "./offlineSoapQueue";

beforeEach(async () => {
  const existing = await listQueuedSoapDrafts();
  await Promise.all(
    existing.map((e) => removeQueuedSoapDraft(e.clientDraftToken)),
  );
});

describe("offlineSoapQueue", () => {
  it("starts empty", async () => {
    expect(await listQueuedSoapDrafts()).toEqual([]);
  });

  it("enqueues and lists a draft", async () => {
    const token = generateClientDraftToken();
    await enqueueSoapDraft({
      clientDraftToken: token,
      appointmentId: "appt-1",
      body: { subjective: "cough" },
      queuedAt: "2026-01-01T00:00:00Z",
    });
    const items = await listQueuedSoapDrafts();
    expect(items).toHaveLength(1);
    expect(items[0].clientDraftToken).toBe(token);
    expect(items[0].appointmentId).toBe("appt-1");
  });

  it("removes a draft by token", async () => {
    const token = generateClientDraftToken();
    await enqueueSoapDraft({
      clientDraftToken: token,
      appointmentId: "appt-1",
      body: {},
      queuedAt: "2026-01-01T00:00:00Z",
    });
    await removeQueuedSoapDraft(token);
    expect(await listQueuedSoapDrafts()).toEqual([]);
  });

  it("overwrites an entry with the same token instead of duplicating", async () => {
    const token = generateClientDraftToken();
    await enqueueSoapDraft({
      clientDraftToken: token,
      appointmentId: "appt-1",
      body: { plan: "v1" },
      queuedAt: "2026-01-01T00:00:00Z",
    });
    await enqueueSoapDraft({
      clientDraftToken: token,
      appointmentId: "appt-1",
      body: { plan: "v2" },
      queuedAt: "2026-01-01T00:05:00Z",
    });
    const items = await listQueuedSoapDrafts();
    expect(items).toHaveLength(1);
    expect(items[0].body).toEqual({ plan: "v2" });
  });

  it("generates unique tokens", () => {
    const a = generateClientDraftToken();
    const b = generateClientDraftToken();
    expect(a).not.toBe(b);
    expect(a.startsWith("offline-")).toBe(true);
  });
});
