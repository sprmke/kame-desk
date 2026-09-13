import "fake-indexeddb/auto";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/apiError";
import {
  enqueueSoapDraft,
  listQueuedSoapDrafts,
  removeQueuedSoapDraft,
} from "./offlineSoapQueue";

vi.mock("@/lib/apiClient", () => ({
  api: { createSoapNote: vi.fn() },
}));

const { api } = await import("@/lib/apiClient");
const { flushQueuedSoapDrafts } = await import("./offlineSoapSync");

beforeEach(async () => {
  vi.mocked(api.createSoapNote).mockReset();
  const existing = await listQueuedSoapDrafts();
  await Promise.all(
    existing.map((e) => removeQueuedSoapDraft(e.clientDraftToken)),
  );
});

describe("flushQueuedSoapDrafts", () => {
  it("does nothing when the queue is empty", async () => {
    const synced = await flushQueuedSoapDrafts();
    expect(synced).toEqual([]);
    expect(api.createSoapNote).not.toHaveBeenCalled();
  });

  it("syncs a queued draft and removes it on success", async () => {
    vi.mocked(api.createSoapNote).mockResolvedValue({ id: "note-1" } as never);
    await enqueueSoapDraft({
      clientDraftToken: "offline-1",
      appointmentId: "appt-1",
      body: { subjective: "cough", client_draft_token: "offline-1" },
      queuedAt: "2026-01-01T00:00:00Z",
    });

    const synced = await flushQueuedSoapDrafts();

    expect(synced).toEqual(["appt-1"]);
    expect(api.createSoapNote).toHaveBeenCalledWith("appt-1", {
      subjective: "cough",
      client_draft_token: "offline-1",
    });
    expect(await listQueuedSoapDrafts()).toEqual([]);
  });

  it("stops at the first failure and leaves later entries queued", async () => {
    vi.mocked(api.createSoapNote)
      .mockRejectedValueOnce(new Error("still offline"))
      .mockResolvedValueOnce({ id: "note-2" } as never);
    await enqueueSoapDraft({
      clientDraftToken: "offline-1",
      appointmentId: "appt-1",
      body: {},
      queuedAt: "2026-01-01T00:00:00Z",
    });
    await enqueueSoapDraft({
      clientDraftToken: "offline-2",
      appointmentId: "appt-2",
      body: {},
      queuedAt: "2026-01-01T00:01:00Z",
    });

    const synced = await flushQueuedSoapDrafts();

    expect(synced).toEqual([]);
    expect(api.createSoapNote).toHaveBeenCalledTimes(1);
    expect(await listQueuedSoapDrafts()).toHaveLength(2);
  });

  it("drops an entry the server permanently rejects and continues past it", async () => {
    vi.mocked(api.createSoapNote)
      .mockRejectedValueOnce(new ApiError("Appointment not found", 404))
      .mockResolvedValueOnce({ id: "note-2" } as never);
    await enqueueSoapDraft({
      clientDraftToken: "offline-1",
      appointmentId: "deleted-appt",
      body: {},
      queuedAt: "2026-01-01T00:00:00Z",
    });
    await enqueueSoapDraft({
      clientDraftToken: "offline-2",
      appointmentId: "appt-2",
      body: {},
      queuedAt: "2026-01-01T00:01:00Z",
    });

    const synced = await flushQueuedSoapDrafts();

    expect(synced).toEqual(["appt-2"]);
    expect(api.createSoapNote).toHaveBeenCalledTimes(2);
    expect(await listQueuedSoapDrafts()).toEqual([]);
  });

  it("retrying the same token twice does not duplicate work once the first succeeds", async () => {
    vi.mocked(api.createSoapNote).mockResolvedValue({ id: "note-1" } as never);
    await enqueueSoapDraft({
      clientDraftToken: "offline-1",
      appointmentId: "appt-1",
      body: {},
      queuedAt: "2026-01-01T00:00:00Z",
    });

    await flushQueuedSoapDrafts();
    const secondRun = await flushQueuedSoapDrafts();

    expect(secondRun).toEqual([]);
    expect(api.createSoapNote).toHaveBeenCalledTimes(1);
  });
});
