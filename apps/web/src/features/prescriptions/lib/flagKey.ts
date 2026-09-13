import type { ConflictFlag } from "@/lib/apiClient";

export function conflictFlagKey(flag: ConflictFlag): string {
  return `${flag.type}:${flag.drug_name}:${flag.message}:${flag.related ?? ""}`;
}
