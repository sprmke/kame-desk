export type ConflictFlag = {
  type: string;
  drug_name: string;
  message: string;
  related?: string | null;
};

export function hasConflicts(flags: ConflictFlag[]) {
  return flags.some((flag) => flag.type !== "unchecked");
}

export function mergeConflictFlags(
  existing: ConflictFlag[],
  incoming: ConflictFlag[],
): ConflictFlag[] {
  const seen = new Set(
    existing.map((f) => `${f.type}:${f.drug_name}:${f.message}`),
  );
  const out = [...existing];
  for (const flag of incoming) {
    const key = `${flag.type}:${flag.drug_name}:${flag.message}`;
    if (!seen.has(key)) {
      seen.add(key);
      out.push(flag);
    }
  }
  return out;
}
