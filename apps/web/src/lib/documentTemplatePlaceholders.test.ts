import { describe, expect, it } from "vitest";
import {
  applyDocumentTemplatePlaceholders,
  enrichDocumentPlaceholders,
  filterDocumentPlaceholders,
  toEditorHtml,
} from "./documentTemplatePlaceholders";
import {
  extractPlaceholderKey,
  highlightPlaceholdersInHtml,
  isKnownTemplatePlaceholderToken,
} from "./templatePlaceholderHighlight";
import { DOCUMENT_PLACEHOLDER_KEY_SET } from "./documentTemplatePlaceholders";

describe("document template placeholders", () => {
  it("extracts dotted keys", () => {
    expect(extractPlaceholderKey("{{patient.full_name}}")).toBe(
      "patient.full_name",
    );
    expect(extractPlaceholderKey("{{bad token}}")).toBeNull();
  });

  it("highlights known tokens in html", () => {
    const html = highlightPlaceholdersInHtml(
      "<p>Hello {{patient.full_name}}</p>",
      DOCUMENT_PLACEHOLDER_KEY_SET,
    );
    expect(html).toContain("template-token-highlight");
    expect(html).toContain("{{patient.full_name}}");
  });

  it("leaves unknown tokens unhighlighted", () => {
    expect(
      isKnownTemplatePlaceholderToken("{{nope}}", DOCUMENT_PLACEHOLDER_KEY_SET),
    ).toBe(false);
  });

  it("wraps plain text for the editor", () => {
    expect(toEditorHtml("Line one\nLine two")).toContain("<p>Line one</p>");
    expect(toEditorHtml("<p>Already html</p>")).toBe("<p>Already html</p>");
  });

  it("rewrites legacy undotted tokens when opening a template", () => {
    expect(
      toEditorHtml(
        "This is to certify that {{patient_name}} was examined on {{visit_date}}.",
      ),
    ).toContain("{{patient.full_name}}");
  });

  it("fills sample names for preview", () => {
    expect(
      applyDocumentTemplatePlaceholders(
        "<p>{{patient.full_name}} at {{clinic.name}}</p>",
      ),
    ).toBe("<p>Maria Santos at Sample Clinic</p>");
  });

  it("enriches placeholders with descriptions and samples", () => {
    const items = enrichDocumentPlaceholders();
    expect(items.length).toBeGreaterThan(0);
    expect(items[0]).toMatchObject({
      token: expect.stringMatching(/^\{\{.+\}\}$/),
      description: expect.any(String),
      example: expect.any(String),
    });
  });

  it("filters placeholders by search query", () => {
    const items = enrichDocumentPlaceholders();
    const filtered = filterDocumentPlaceholders(items, "patient.full");
    expect(filtered.some((item) => item.key === "patient.full_name")).toBe(
      true,
    );
    expect(filtered.every((item) => item.key.includes("patient"))).toBe(true);
  });
});
