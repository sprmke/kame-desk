import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

export type LoginValues = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  full_name: z.string().min(1, "Full name is required"),
  clinic_name: z.string().min(1, "Clinic name is required"),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "At least 8 characters"),
});

export type RegisterValues = z.infer<typeof registerSchema>;
