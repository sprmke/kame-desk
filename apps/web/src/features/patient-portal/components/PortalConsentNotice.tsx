import { useState } from "react";
import { ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  ackPortalConsent,
  hasAckedPortalConsent,
} from "@/lib/patientPortalAuth";

export function PortalConsentNotice() {
  const [acked, setAcked] = useState(hasAckedPortalConsent());
  if (acked) return null;

  return (
    <Card className="mb-4 border-primary/30 bg-primary/5">
      <CardContent className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-3">
          <ShieldCheck
            className="mt-0.5 size-5 shrink-0 text-primary"
            aria-hidden
          />
          <p className="text-sm text-foreground">
            This portal shows your own medical records. Only you can see this
            information — keep your login link private and log out on shared
            devices.
          </p>
        </div>
        <Button
          size="sm"
          className="shrink-0"
          onClick={() => {
            ackPortalConsent();
            setAcked(true);
          }}
        >
          Got it
        </Button>
      </CardContent>
    </Card>
  );
}
