import { Link } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useEffect } from "react";
import { api } from "@/lib/apiClient";
import { AuthLayout } from "@/features/auth/components/AuthLayout";
import { Button } from "@/components/ui/button";

export function VerifyEmailPage({ token }: { token: string }) {
  const verify = useMutation({
    mutationFn: () => api.verifyEmail(token),
  });

  useEffect(() => {
    if (token) verify.mutate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  if (!token) {
    return (
      <AuthLayout title="Verify email">
        <p className="text-sm text-muted-foreground">
          This verification link is missing.
        </p>
        <p className="mt-6 text-center text-sm">
          <Link
            to="/login"
            className="font-medium text-primary hover:underline"
          >
            Sign in
          </Link>
        </p>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Verify email">
      {verify.isPending && (
        <p className="text-sm text-muted-foreground">Verifying…</p>
      )}
      {verify.isSuccess && (
        <p className="text-sm text-foreground">
          Email verified. You can sign in.
        </p>
      )}
      {verify.isError && (
        <p className="text-sm text-destructive">
          This link is invalid or expired.
        </p>
      )}
      <div className="mt-6">
        <Button asChild className="w-full">
          <Link to="/login">Sign in</Link>
        </Button>
      </div>
    </AuthLayout>
  );
}
