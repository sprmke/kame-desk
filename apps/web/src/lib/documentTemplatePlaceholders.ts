/** Keep in sync with `TEMPLATE_PLACEHOLDERS` in `apps/api/app/services/template_renderer.py`. */

import {
  DOCUMENT_TOKEN_PATTERN,
  LEGACY_DOCUMENT_PLACEHOLDER_ALIASES,
} from "@/lib/templatePlaceholderHighlight";

export type PlaceholderGroup = {
  id: string;
  label: string;
  keys: readonly string[];
};

export const DOCUMENT_PLACEHOLDER_GROUPS: readonly PlaceholderGroup[] = [
  {
    id: "patient",
    label: "Patient",
    keys: [
      "patient.full_name",
      "patient.birthdate",
      "patient.contact_number",
      "patient.address",
    ],
  },
  {
    id: "clinic",
    label: "Clinic",
    keys: ["clinic.name", "clinic.address", "clinic.contact_phone"],
  },
  {
    id: "doctor",
    label: "Doctor",
    keys: ["doctor.full_name", "doctor.specialty", "doctor.prc_license_number"],
  },
  {
    id: "visit",
    label: "Visit",
    keys: ["visit.date", "visit.reason_for_visit"],
  },
];

export const DOCUMENT_PLACEHOLDER_KEYS: readonly string[] =
  DOCUMENT_PLACEHOLDER_GROUPS.flatMap((group) => [...group.keys]);

export const DOCUMENT_PLACEHOLDER_KEY_SET: ReadonlySet<string> = new Set(
  DOCUMENT_PLACEHOLDER_KEYS,
);

/** Short labels for the placeholder picker. */
export const DOCUMENT_PLACEHOLDER_DESCRIPTIONS: Readonly<
  Record<string, string>
> = {
  "patient.full_name": "Patient name",
  "patient.birthdate": "Date of birth",
  "patient.contact_number": "Phone number",
  "patient.address": "Home address",
  "clinic.name": "Clinic name",
  "clinic.address": "Clinic address",
  "clinic.contact_phone": "Clinic phone",
  "doctor.full_name": "Doctor name",
  "doctor.specialty": "Specialty",
  "doctor.prc_license_number": "PRC license",
  "visit.date": "Visit date",
  "visit.reason_for_visit": "Reason for visit",
};

export type EnrichedPlaceholder = {
  key: string;
  token: string;
  group: string;
  description: string;
  example: string;
};

export function enrichDocumentPlaceholders(
  groups: readonly PlaceholderGroup[] = DOCUMENT_PLACEHOLDER_GROUPS,
  sampleValues: Readonly<
    Record<string, string>
  > = SAMPLE_DOCUMENT_TEMPLATE_VALUES,
): EnrichedPlaceholder[] {
  return groups.flatMap((group) =>
    group.keys.map((key) => ({
      key,
      token: placeholderToken(key),
      group: group.label,
      description: DOCUMENT_PLACEHOLDER_DESCRIPTIONS[key] ?? key,
      example: sampleValues[key] ?? "",
    })),
  );
}

export function filterDocumentPlaceholders(
  items: EnrichedPlaceholder[],
  query: string,
): EnrichedPlaceholder[] {
  const q = query.trim().toLowerCase();
  if (!q) return items;
  return items.filter(
    (item) =>
      item.key.toLowerCase().includes(q) ||
      item.token.toLowerCase().includes(q) ||
      item.description.toLowerCase().includes(q),
  );
}

export function groupDocumentPlaceholders(
  items: EnrichedPlaceholder[],
): { group: string; items: EnrichedPlaceholder[] }[] {
  const map = new Map<string, EnrichedPlaceholder[]>();
  for (const item of items) {
    const list = map.get(item.group) ?? [];
    list.push(item);
    map.set(item.group, list);
  }
  return [...map.entries()].map(([group, groupItems]) => ({
    group,
    items: groupItems,
  }));
}

export function placeholderToken(key: string): string {
  return `{{${key}}}`;
}

export function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

/** Wrap plain-text templates so TipTap can edit them. HTML bodies pass through. */
export function migrateLegacyPlaceholderTokens(html: string): string {
  DOCUMENT_TOKEN_PATTERN.lastIndex = 0;
  return html.replace(DOCUMENT_TOKEN_PATTERN, (match) => {
    const key = match.slice(2, -2);
    const canonical = LEGACY_DOCUMENT_PLACEHOLDER_ALIASES[key];
    return canonical ? `{{${canonical}}}` : match;
  });
}

export function toEditorHtml(body: string): string {
  const trimmed = body.trim();
  if (!trimmed) return "<p></p>";
  const html = /<[a-z][\s\S]*>/i.test(trimmed)
    ? body
    : trimmed
        .split("\n")
        .map((line) => `<p>${escapeHtml(line) || "<br>"}</p>`)
        .join("");
  return migrateLegacyPlaceholderTokens(html);
}

export const DEFAULT_DOCUMENT_TEMPLATE_HTML =
  "<p>This certifies that {{patient.full_name}} was seen at {{clinic.name}} on {{visit.date}}.</p>";

/** Keep in sync with `SAMPLE_TEMPLATE_CONTEXT` in `template_renderer.py`. */
export const SAMPLE_DOCUMENT_TEMPLATE_VALUES: Readonly<Record<string, string>> =
  {
    "patient.full_name": "Maria Santos",
    "patient.birthdate": "1988-03-12",
    "patient.contact_number": "+639171000000",
    "patient.address": "Makati",
    "clinic.name": "Sample Clinic",
    "clinic.address": "123 Clinic St",
    "clinic.contact_phone": "+63281234567",
    "doctor.full_name": "Dr Santos",
    "doctor.specialty": "General Practice",
    "doctor.prc_license_number": "PRC-0000",
    "visit.date": "2026-09-11",
    "visit.reason_for_visit": "Follow-up",
  };

export function applyDocumentTemplatePlaceholders(html: string): string {
  DOCUMENT_TOKEN_PATTERN.lastIndex = 0;
  return html.replace(DOCUMENT_TOKEN_PATTERN, (match) => {
    const key = match.slice(2, -2);
    const canonical = LEGACY_DOCUMENT_PLACEHOLDER_ALIASES[key] ?? key;
    return SAMPLE_DOCUMENT_TEMPLATE_VALUES[canonical] ?? "";
  });
}
