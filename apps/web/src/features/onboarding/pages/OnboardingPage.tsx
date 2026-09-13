import { useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ProductMark } from "@/components/brand/ProductMark";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Stepper } from "@/components/ui/stepper";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { ClinicStep } from "../components/ClinicStep";
import { DoctorStep } from "../components/DoctorStep";
import { HoursStep } from "../components/HoursStep";
import { FeesStep } from "../components/FeesStep";
import { InviteStep } from "../components/InviteStep";
import { useOnboardingStatus } from "../hooks/useOnboarding";
import { resumeOnboardingStep } from "../lib/resumeStep";
import { OnboardingSkeleton } from "@/components/skeletons/PageSkeletons";

const ORDER = ["clinic", "doctor", "hours", "fees", "invite"] as const;

const STEP_META: Record<
  (typeof ORDER)[number],
  { label: string; title: string; description: string }
> = {
  clinic: {
    label: "Clinic",
    title: "Clinic profile",
    description: "Contact details patients and staff will see.",
  },
  doctor: {
    label: "Doctor",
    title: "Doctor profile",
    description: "Specialty, license, and default fees.",
  },
  hours: {
    label: "Hours",
    title: "Operating hours",
    description: "Set your weekly schedule for booking.",
  },
  fees: {
    label: "Fees",
    title: "Service fees",
    description: "Add a service and its price.",
  },
  invite: {
    label: "Invite",
    title: "Invite your team",
    description: "Bring in front desk staff or other doctors.",
  },
};

export function OnboardingPage() {
  const navigate = useNavigate();
  const { data, isLoading } = useOnboardingStatus();
  const [step, setStep] = useState<string>("clinic");

  useEffect(() => {
    if (data) setStep(resumeOnboardingStep(data));
    if (data?.all_complete) navigate({ to: "/dashboard" });
  }, [data, navigate]);

  function next() {
    const idx = ORDER.indexOf(step as (typeof ORDER)[number]);
    const nextStep = ORDER[idx + 1];
    if (nextStep) setStep(nextStep);
    else navigate({ to: "/dashboard" });
  }

  if (isLoading) {
    return (
      <main className="relative flex min-h-screen items-center justify-center bg-muted/40 p-6">
        <div className="absolute top-4 right-4">
          <ThemeToggle />
        </div>
        <OnboardingSkeleton />
      </main>
    );
  }

  const meta = STEP_META[step as (typeof ORDER)[number]];

  return (
    <main className="relative flex min-h-screen items-center justify-center bg-muted/40 p-4 sm:p-6">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      <div className="flex w-full max-w-2xl flex-col gap-6">
        <div className="flex items-center justify-center gap-2">
          <span className="flex size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <ProductMark className="size-5" />
          </span>
          <span className="text-lg font-semibold text-foreground">
            DoctorDesk
          </span>
        </div>

        <Stepper
          activeId={step}
          steps={ORDER.map((key) => ({
            id: key,
            label: STEP_META[key].label,
          }))}
        />

        <Card>
          <CardHeader>
            <CardTitle>{meta.title}</CardTitle>
            <p className="text-sm text-muted-foreground">{meta.description}</p>
          </CardHeader>
          <CardContent>
            {step === "clinic" && <ClinicStep onNext={next} />}
            {step === "doctor" && <DoctorStep onNext={next} />}
            {step === "hours" && <HoursStep onNext={next} />}
            {step === "fees" && <FeesStep onNext={next} />}
            {step === "invite" && (
              <InviteStep onDone={() => navigate({ to: "/dashboard" })} />
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
