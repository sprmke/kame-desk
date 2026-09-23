export type DoctorSpecialty = {
  key: string;
  label: string;
  soapTemplateKey: string;
};

export const DOCTOR_SPECIALTIES: DoctorSpecialty[] = [
  { key: "dentist", label: "Dentist", soapTemplateKey: "dental" },
  { key: "obgyn", label: "OB-GYN", soapTemplateKey: "obgyn" },
  {
    key: "pediatrician",
    label: "Pediatrician",
    soapTemplateKey: "pediatric",
  },
  {
    key: "general_practitioner",
    label: "General practitioner",
    soapTemplateKey: "general",
  },
  {
    key: "dermatologist",
    label: "Dermatologist",
    soapTemplateKey: "dermatology",
  },
  { key: "cardiologist", label: "Cardiologist", soapTemplateKey: "general" },
  {
    key: "ophthalmologist",
    label: "Ophthalmologist",
    soapTemplateKey: "general",
  },
  { key: "orthopedic", label: "Orthopedic", soapTemplateKey: "general" },
  { key: "ent", label: "ENT", soapTemplateKey: "general" },
  { key: "other", label: "Other", soapTemplateKey: "general" },
];

export function soapTemplateForSpecialtyKey(
  key: string | null | undefined,
): string {
  return (
    DOCTOR_SPECIALTIES.find((item) => item.key === key)?.soapTemplateKey ??
    "general"
  );
}

export function specialtyKeyFromLegacyLabel(
  label: string | null | undefined,
): string {
  if (!label?.trim()) return "";
  const match = DOCTOR_SPECIALTIES.find(
    (item) => item.label.toLowerCase() === label.trim().toLowerCase(),
  );
  return match?.key ?? "other";
}
