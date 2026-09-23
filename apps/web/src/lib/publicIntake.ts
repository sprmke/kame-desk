export const PUBLIC_INTAKE_KEYS = [
  "email",
  "birthdate",
  "sex",
  "address",
  "reason",
  "existing_patient",
  "notes",
] as const;

export type PublicIntakeKey = (typeof PUBLIC_INTAKE_KEYS)[number];

export type PublicIntakeFields = Record<PublicIntakeKey, boolean>;

export const DEFAULT_PUBLIC_INTAKE: PublicIntakeFields = {
  email: false,
  birthdate: false,
  sex: false,
  address: false,
  reason: false,
  existing_patient: false,
  notes: false,
};

export const PUBLIC_INTAKE_LABELS: Record<PublicIntakeKey, string> = {
  email: "Email",
  birthdate: "Birthdate",
  sex: "Sex",
  address: "Address",
  reason: "Reason",
  existing_patient: "New or existing",
  notes: "Notes",
};

export function normalizePublicIntake(
  raw?: Record<string, boolean> | null,
): PublicIntakeFields {
  return {
    email: Boolean(raw?.email),
    birthdate: Boolean(raw?.birthdate),
    sex: Boolean(raw?.sex),
    address: Boolean(raw?.address),
    reason: Boolean(raw?.reason),
    existing_patient: Boolean(raw?.existing_patient),
    notes: Boolean(raw?.notes),
  };
}
