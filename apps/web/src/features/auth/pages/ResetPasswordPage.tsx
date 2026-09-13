import { Link, useNavigate } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api } from "@/lib/apiClient";
import { ApiError } from "@/lib/apiError";
import { AuthLayout } from "@/features/auth/components/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field, FieldError } from "@/components/forms/Field";
import { FieldLabel } from "@/components/forms/FieldLabel";

const schema = z.object({
  password: z.string().min(8, "At least 8 characters"),
});

type Values = z.infer<typeof schema>;

export function ResetPasswordPage({ token }: { token: string }) {
  const navigate = useNavigate();
  const form = useForm<Values>({ resolver: zodResolver(schema) });
  const reset = useMutation({
    mutationFn: (values: Values) => api.resetPassword(token, values.password),
    onSuccess: () => navigate({ to: "/login" }),
  });

  if (!token) {
    return (
      <AuthLayout title="Reset password">
        <p className="text-sm text-muted-foreground">
          This reset link is missing or invalid.
        </p>
        <p className="mt-6 text-center text-sm">
          <Link
            to="/forgot-password"
            className="font-medium text-primary hover:underline"
          >
            Request a new link
          </Link>
        </p>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Set a new password">
      <form
        className="flex flex-col gap-4"
        onSubmit={form.handleSubmit((v) => reset.mutate(v))}
      >
        <Field>
          <FieldLabel htmlFor="password" label="New password" required />
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            placeholder="••••••••"
            {...form.register("password")}
          />
          <FieldError>{form.formState.errors.password?.message}</FieldError>
        </Field>
        {reset.isError && (
          <p className="text-sm text-destructive">
            {reset.error instanceof ApiError
              ? reset.error.message
              : "Reset failed. Request a new link."}
          </p>
        )}
        <Button type="submit" disabled={reset.isPending}>
          {reset.isPending ? "Saving…" : "Save password"}
        </Button>
      </form>
    </AuthLayout>
  );
}
