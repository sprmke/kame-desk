import { describe, expect, it } from "vitest";
import {
  LIST_DEFAULT_PAGE_SIZE,
  buildPageItems,
  listRange,
  normalizeListPageLimit,
} from "./pagination";

describe("normalizeListPageLimit", () => {
  it("keeps allowed sizes", () => {
    expect(normalizeListPageLimit(50)).toBe(50);
  });

  it("falls back to 25", () => {
    expect(normalizeListPageLimit(12)).toBe(LIST_DEFAULT_PAGE_SIZE);
  });
});

describe("listRange", () => {
  it("returns empty bounds when total is 0", () => {
    expect(listRange(1, 25, 0)).toEqual({
      startIdx: 0,
      endIdx: 0,
      pageCount: 1,
    });
  });

  it("clamps page into range", () => {
    expect(listRange(9, 25, 40)).toEqual({
      startIdx: 26,
      endIdx: 40,
      pageCount: 2,
    });
  });
});

describe("buildPageItems", () => {
  it("lists every page when total is small", () => {
    expect(buildPageItems(1, 4)).toEqual([1, 2, 3, 4]);
  });

  it("inserts ellipsis around the current page", () => {
    expect(buildPageItems(5, 12)).toEqual([
      1,
      "ellipsis",
      4,
      5,
      6,
      "ellipsis",
      12,
    ]);
  });
});
