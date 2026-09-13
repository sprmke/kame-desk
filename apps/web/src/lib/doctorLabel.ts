export function doctorLabel(doctor: {
  full_name?: string | null;
  specialty?: string | null;
}): string {
  const name = doctor.full_name?.trim();
  return name || "Doctor";
}
