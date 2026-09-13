import { useMutation } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { useNavigate } from "@tanstack/react-router";
import { AuthLayout } from "@/features/auth/components/AuthLayout";
import { Button } from "@/components/ui/button";
import { patientPortalApi } from "@/features/patient-portal/lib/patientPortalClient";

export function PatientPortalVerifyPage({
  slug,
  token,
}: {
  slug: string;
  token: string | undefined;
}) {
  const navigate = useNavigate();
  const attempted = useRef(false);

  const verify = useMutation({
    mutationFn: (t: string) => patientPortalApi.verifyLogin(t),
    onSuccess: () => {
      navigate({ to: `/patient-portal/${slug}/visits` });
    },
  });

  useEffect(() => {
    if (!token || attempted.current) return;
    attempted.current = true;
    verify.mutate(token);
  }, [token, verify]);

  if (!token) {
    return (
      <AuthLayout title="Invalid login link">
        <p className="text-sm text-muted-foreground">
          This link is missing its login token. Request a new one.
        </p>
        <Button
          className="mt-4 w-full"
          onClick={() => navigate({ to: `/patient-portal/${slug}/login` })}
        >
          Back to login
        </Button>
      </AuthLayout>
    );
  }

  if (verify.isError) {
    return (
      <AuthLayout title="Link expired or already used">
        <p className="text-sm text-muted-foreground">
          This login link is no longer valid. Request a new one.
        </p>
        <Button
          className="mt-4 w-full"
          onClick={() => navigate({ to: `/patient-portal/${slug}/login` })}
        >
          Back to login
        </Button>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Signing you in…">
      <p className="text-sm text-muted-foreground">One moment.</p>
    </AuthLayout>
  );
}
