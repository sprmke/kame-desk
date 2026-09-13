import { Link, useNavigate } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/apiClient";
import { ApiError } from "@/lib/apiError";
import { saveAuth } from "@/lib/auth";
import { defaultLandingPath, type ClinicRole } from "@/lib/rbac";
import { AuthLayout } from "@/features/auth/components/AuthLayout";
import { loginSchema, type LoginValues } from "@/features/auth/lib/schemas";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field, FieldError } from "@/components/forms/Field";
import { FieldLabel } from "@/components/forms/FieldLabel";

export function LoginPage() {
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) });

  const login = useMutation({
    mutationFn: (values: LoginValues) => api.login(values),
    onSuccess: (res) => {
      saveAuth(res.tokens, res.clinic_id);
      navigate({
        to: defaultLandingPath(res.role as ClinicRole),
      });
    },
  });

  return (
    <AuthLayout title="Sign in">
      <form
        className="flex flex-col gap-4"
        onSubmit={handleSubmit((values) => login.mutate(values))}
      >
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
            autoComplete="current-password"
            placeholder="••••••••"
            {...register("password")}
          />
          <FieldError>{errors.password?.message}</FieldError>
        </Field>

        {login.isError && (
          <p className="text-sm text-destructive">
            {login.error instanceof ApiError
              ? login.error.message
              : "Sign in failed. Check your credentials."}
          </p>
        )}

        <Button type="submit" className="mt-1" disabled={login.isPending}>
          {login.isPending ? "Signing in…" : "Sign in"}
        </Button>
      </form>

      <p className="mt-4 text-center text-sm">
        <Link
          to="/forgot-password"
          className="font-medium text-primary hover:underline"
        >
          Forgot password
        </Link>
      </p>

      <p className="mt-4 text-center text-sm text-muted-foreground">
        No account?{" "}
        <Link
          to="/register"
          className="font-medium text-primary hover:underline"
        >
          Register your clinic
        </Link>
      </p>
    </AuthLayout>
  );
}
