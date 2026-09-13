import { z } from "zod";

export const patientFormSchema = z.object({
  data_processing_consent: z
    .boolean()
    .refine((v) => v, { message: "Required" }),
  full_name: z.string().min(1, "Required"),
  birthdate: z.string().optional(),
  sex: z.string().optional(),
  civil_status: z.string().optional(),
  occupation: z.string().optional(),
  contact_number: z.string().optional(),
  email: z.string().email().optional().or(z.literal("")),
  address: z.string().optional(),
  insurance_provider: z.string().optional(),
  insurance_member_id: z.string().optional(),
});

export type PatientFormValues = z.infer<typeof patientFormSchema>;
