import { z } from "zod";

export const clinicProfileSchema = z.object({
  address: z.string().min(1),
  contact_phone: z.string().min(1),
  contact_email: z.string().email(),
  license_info: z.string().min(1),
  accreditation_info: z.string().optional(),
});

export const doctorProfileSchema = z.object({
  specialty: z.string().min(1),
  prc_license_number: z.string().min(1),
  consultation_fee: z.coerce.number().min(0),
  follow_up_fee: z.coerce.number().min(0).optional(),
});

export const feeSchema = z.object({
  name: z.string().min(1),
  amount: z.coerce.number().min(0),
});

export const inviteSchema = z.object({
  email: z.string().email(),
  role: z.enum(["admin", "doctor", "reception"]),
});

export const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"] as const;

export const defaultHours = () =>
  Object.fromEntries(
    DAYS.map((d) => [
      d,
      { open: "09:00", close: "17:00", closed: d === "sun" },
    ]),
  );
