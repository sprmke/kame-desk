import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { MailCheck } from "lucide-react";
import { ProductMark } from "@/components/brand/ProductMark";
import { AuthLayout } from "@/features/auth/components/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { InlineError } from "@/components/ErrorState";
import { patientPortalApi } from "@/features/patient-portal/lib/patientPortalClient";

export function PatientPortalLoginPage({ slug }: { slug: string }) {
  const [identifier, setIdentifier] = useState("");

  const request = useMutation({
    mutationFn: () => patientPortalApi.requestLogin(slug, identifier),
  });

  if (request.isSuccess) {
    return (
      <AuthLayout title="Check your email or phone">
        <div className="flex flex-col items-center gap-3 py-4 text-center">
          <MailCheck className="size-8 text-primary" aria-hidden />
          <p className="text-sm text-muted-foreground">
            If that matches a record on file, we sent a one-time login link. It
            expires in 15 minutes.
          </p>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Patient Portal login">
      <form
        className="flex flex-col gap-4"
        onSubmit={(e) => {
          e.preventDefault();
          request.mutate();
        }}
      >
        <p className="text-sm text-muted-foreground">
          Enter the email or mobile number on file with your clinic and
          we&apos;ll send you a secure login link.
        </p>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="identifier">Email or mobile number</Label>
          <Input
            id="identifier"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            placeholder="you@example.com or 09171234567"
            autoFocus
            required
          />
        </div>
        {request.isError ? (
          <InlineError heading="Could not send the login link. Try again." />
        ) : null}
        <Button type="submit" disabled={request.isPending || !identifier}>
          {request.isPending ? "Sending…" : "Send login link"}
        </Button>
      </form>
      <div className="mt-6 flex items-center justify-center gap-2 text-xs text-muted-foreground">
        <ProductMark className="size-3.5" />
        <span>Powered by DoctorDesk</span>
      </div>
    </AuthLayout>
  );
}
