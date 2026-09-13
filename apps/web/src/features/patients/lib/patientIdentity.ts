export function ageYears(birthdate: string | null | undefined): number | null {
  if (!birthdate) return null;
  const birth = new Date(`${birthdate}T00:00:00+08:00`);
  if (Number.isNaN(birth.getTime())) return null;
  const now = new Date();
  let years = now.getFullYear() - birth.getFullYear();
  const monthDelta = now.getMonth() - birth.getMonth();
  if (monthDelta < 0 || (monthDelta === 0 && now.getDate() < birth.getDate())) {
    years -= 1;
  }
  return years >= 0 ? years : null;
}

export function patientDisambiguator(patient: {
  birthdate: string | null;
  sex: string | null;
  contact_number: string | null;
}): string | null {
  const bits: string[] = [];
  const years = ageYears(patient.birthdate);
  if (years != null) bits.push(`${years}y`);
  if (patient.sex) bits.push(patient.sex);
  if (patient.contact_number) bits.push(patient.contact_number);
  return bits.length ? bits.join(" · ") : null;
}
