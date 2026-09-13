import { Link, useNavigate, useSearch } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/apiClient";
import { ApiError } from "@/lib/apiError";
import { saveAuth } from "@/lib/auth";
import { AuthLayout } from "@/features/auth/components/AuthLayout";
import {
  registerSchema,
  type RegisterValues,
} from "@/features/auth/lib/schemas";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field, FieldError } from "@/components/forms/Field";
import { FieldLabel } from "@/components/forms/FieldLabel";

export function RegisterPage() {
  const navigate = useNavigate();
  const { plan } = useSearch({ strict: false }) as { plan?: string };
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) });

  const registerClinic = useMutation({
    mutationFn: (values: RegisterValues) =>
      api.register({
        ...values,
        plan_key:
          plan === "starter" || plan === "pro" || plan === "clinic"
            ? plan
            : undefined,
      }),
    onSuccess: (res) => {
      saveAuth(res.tokens, res.clinic_id);
      navigate({ to: "/onboarding" });
    },
  });

  return (
    <AuthLayout title="Register your clinic">
      <form
        className="flex flex-col gap-4"
        onSubmit={handleSubmit((values) => registerClinic.mutate(values))}
      >
        <Field>
          <FieldLabel htmlFor="full_name" label="Your name" required />
          <Input
            id="full_name"
            autoComplete="name"
            placeholder={FORM_PLACEHOLDERS.fullName}
            {...register("full_name")}
          />
          <FieldError>{errors.full_name?.message}</FieldError>
        </Field>
        <Field>
          <FieldLabel htmlFor="clinic_name" label="Clinic name" required />
          <Input
            id="clinic_name"
            placeholder={FORM_PLACEHOLDERS.clinicName}
            {...register("clinic_name")}
          />
          <FieldError>{errors.clinic_name?.message}</FieldError>
        </Field>
        <Field>
          <FieldLabel htmlFor="email" label="Email" required />
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder={FORM_PLACEHOLDERS.email}
            {...register("email")}
          />
          <FieldError>{errors.email?.message}</FieldError>
        </Field>
        <Field>
          <FieldLabel htmlFor="password" label="Password" required />
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            placeholder="••••••••"
            {...register("password")}
          />
          <FieldError>{errors.password?.message}</FieldError>
        </Field>

        {registerClinic.isError && (
          <p className="text-sm text-destructive">
            {registerClinic.error instanceof ApiError
              ? registerClinic.error.message
              : "Registration failed."}
          </p>
        )}

        <Button
          type="submit"
          className="mt-1"
          disabled={registerClinic.isPending}
        >
          {registerClinic.isPending ? "Creating clinic…" : "Create clinic"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link to="/login" className="font-medium text-primary hover:underline">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
