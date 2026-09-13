const FORBIDDEN = new Set([
  "patient_id",
  "patient_name",
  "full_name",
  "contact_number",
  "email",
  "reason_for_visit",
  "soap",
  "diagnosis",
  "allergies",
]);

export function sanitize_grounding_facts(
  payload: Record<string, unknown>,
): Record<string, unknown> {
  function walk(value: unknown): unknown {
    if (Array.isArray(value)) return value.map(walk);
    if (value && typeof value === "object") {
      const out: Record<string, unknown> = {};
      for (const [key, inner] of Object.entries(value)) {
        if (FORBIDDEN.has(key)) continue;
        out[key] = walk(inner);
      }
      return out;
    }
    return value;
  }
  return walk(payload) as Record<string, unknown>;
}
