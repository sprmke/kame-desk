import { z } from "zod";

export const clinicProfileSchema = z.object({
  address: z.string().min(1),
  contact_phone: z.string().min(1),
  contact_email: z.string().email(),
  license_info: z.string().min(1),
  accreditation_info: z.string().optional(),
});

export const doctorProfileSchema = z
  .object({
    specialty_key: z.string().min(1, "Specialty is required"),
    specialty_other: z.string().max(128).optional(),
    prc_license_number: z.string().min(1),
    consultation_fee: z.coerce.number().min(0),
    follow_up_fee: z.coerce.number().min(0).optional(),
  })
  .superRefine((data, ctx) => {
    if (data.specialty_key === "other" && !data.specialty_other?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Enter a specialty",
        path: ["specialty_other"],
      });
    }
  });

export type DoctorProfileValues = z.infer<typeof doctorProfileSchema>;

export const feeSchema = z.object({
  name: z.string().min(1),
  amount: z.coerce.number().min(0),
});

export const inviteSchema = z.object({
  email: z.string().email(),
  role: z.enum(["admin", "doctor", "reception"]),
});

export const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"] as const;

export type WorkingHoursDay = {
  open: string;
  close: string;
  closed: boolean;
  breaks?: { start: string; end: string }[];
};

export const defaultHours = (): Record<
  (typeof DAYS)[number],
  WorkingHoursDay
> =>
  Object.fromEntries(
    DAYS.map((d) => [
      d,
      { open: "09:00", close: "17:00", closed: d === "sun" },
    ]),
  ) as Record<(typeof DAYS)[number], WorkingHoursDay>;
