import { z } from "zod";

export const appointmentFormSchema = z.object({
  patient_id: z.string().min(1, "Required"),
  doctor_id: z.string().min(1, "Required"),
  room_id: z.string().optional(),
  service_fee_id: z.string().optional(),
  date: z.string().min(1, "Required"),
  time: z.string().min(1, "Required"),
  duration_minutes: z.coerce.number().min(5).max(480),
  reason_for_visit: z.string().optional(),
  notes: z.string().optional(),
});

export type AppointmentFormValues = z.infer<typeof appointmentFormSchema>;
