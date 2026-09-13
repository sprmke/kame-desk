import { Link, useNavigate } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api } from "@/lib/apiClient";
import { AuthLayout } from "@/features/auth/components/AuthLayout";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field, FieldError } from "@/components/forms/Field";
import { FieldLabel } from "@/components/forms/FieldLabel";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
});

type Values = z.infer<typeof schema>;

export function ForgotPasswordPage() {
  const navigate = useNavigate();
  const form = useForm<Values>({ resolver: zodResolver(schema) });
  const send = useMutation({
    mutationFn: (values: Values) => api.forgotPassword(values.email),
    onSuccess: () => navigate({ to: "/login" }),
  });

  return (
    <AuthLayout title="Reset password">
      <form
        className="flex flex-col gap-4"
        onSubmit={form.handleSubmit((v) => send.mutate(v))}
      >
        <Field>
          <FieldLabel htmlFor="email" label="Email" required />
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder={FORM_PLACEHOLDERS.email}
            {...form.register("email")}
          />
          <FieldError>{form.formState.errors.email?.message}</FieldError>
        </Field>
        <Button type="submit" disabled={send.isPending}>
          {send.isPending ? "Sending…" : "Send link"}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted-foreground">
        <Link to="/login" className="font-medium text-primary hover:underline">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
