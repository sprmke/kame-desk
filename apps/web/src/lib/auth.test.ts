import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { isAuthenticated, saveAuth, shouldDeferAuthRedirect } from "@/lib/auth";

describe("auth", () => {
  const store = new Map<string, string>();

  beforeEach(() => {
    store.clear();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      },
      clear: () => {
        store.clear();
      },
    });
    vi.stubGlobal("window", globalThis);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("isAuthenticated is false without tokens", () => {
    expect(isAuthenticated()).toBe(false);
  });

  it("isAuthenticated is true when access token is stored", () => {
    saveAuth(
      { access_token: "test-access", refresh_token: "test-refresh" },
      "clinic-1",
    );
    expect(isAuthenticated()).toBe(true);
  });

  it("shouldDeferAuthRedirect is true without window", () => {
    vi.stubGlobal("window", undefined);
    expect(shouldDeferAuthRedirect()).toBe(true);
    expect(isAuthenticated()).toBe(false);
  });
});
