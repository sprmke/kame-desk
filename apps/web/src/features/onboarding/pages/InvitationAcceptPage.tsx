import { useNavigate } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/apiClient";
import { ApiError } from "@/lib/apiError";
import { AuthLayout } from "@/features/auth/components/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function InvitationAcceptPage({ token }: { token: string }) {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");

  const accept = useMutation({
    mutationFn: () =>
      api.acceptInvitation(token, {
        full_name: fullName || undefined,
        password: password || undefined,
      }),
    onSuccess: () => navigate({ to: "/login" }),
  });

  if (!token) {
    return (
      <AuthLayout title="Invitation">
        <p className="text-sm text-muted-foreground">
          Missing invitation token.
        </p>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Join your clinic">
      <form
        className="flex flex-col gap-4"
        onSubmit={(e) => {
          e.preventDefault();
          accept.mutate();
        }}
      >
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="full_name">Full name</Label>
          <Input
            id="full_name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="password">Set a password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        {accept.isError && (
          <p className="text-sm text-destructive">
            {accept.error instanceof ApiError
              ? accept.error.message
              : "Could not accept invitation."}
          </p>
        )}
        {accept.isSuccess && (
          <p className="text-sm text-success">
            Invitation accepted. Sign in to continue.
          </p>
        )}

        <Button type="submit" disabled={accept.isPending}>
          {accept.isPending ? "Joining…" : "Accept invitation"}
        </Button>
      </form>
    </AuthLayout>
  );
}
