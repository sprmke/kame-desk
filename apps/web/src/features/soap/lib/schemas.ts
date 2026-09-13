import { z } from "zod";
import { ICD10_SUGGESTIONS } from "./icd10Suggestions";

export const soapFormSchema = z.object({
  subjective: z.string().optional(),
  objective: z.string().optional(),
  assessment: z.string().optional(),
  plan: z.string().optional(),
  diagnosis_primary: z.string().optional(),
  icd10_codes: z.array(z.string()).optional(),
  follow_up_date: z.string().optional(),
  specialty_template_key: z.string().optional(),
  specialty_data: z.record(z.unknown()).optional(),
});

export type SoapFormValues = z.infer<typeof soapFormSchema>;

export function filterIcd10(query: string) {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  return ICD10_SUGGESTIONS.filter(
    (item) =>
      item.code.toLowerCase().includes(q) ||
      item.label.toLowerCase().includes(q),
  ).slice(0, 8);
}
