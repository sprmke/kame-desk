import { useState } from "react";
import { DAYS, defaultHours } from "../lib/schemas";
import { useOnboardingMutations } from "../hooks/useOnboarding";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { TimePicker } from "@/components/ui/time-picker";

type Props = { onNext: () => void };

const DAY_LABELS: Record<string, string> = {
  mon: "Monday",
  tue: "Tuesday",
  wed: "Wednesday",
  thu: "Thursday",
  fri: "Friday",
  sat: "Saturday",
  sun: "Sunday",
};

export function HoursStep({ onNext }: Props) {
  const { saveHours } = useOnboardingMutations();
  const [hours, setHours] = useState(defaultHours());

  async function submit() {
    await saveHours.mutateAsync({ working_hours: hours, holiday_dates: [] });
    onNext();
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col divide-y divide-border rounded-lg border border-border">
        {DAYS.map((day) => (
          <div
            key={day}
            className="flex flex-wrap items-center gap-3 px-3 py-2.5 sm:gap-4"
          >
            <span className="w-24 shrink-0 text-sm font-medium text-foreground">
              {DAY_LABELS[day]}
            </span>
            <div className="flex items-center gap-2">
              <TimePicker
                className="h-9 w-32"
                aria-label={`${DAY_LABELS[day]} open`}
                value={hours[day].open}
                disabled={hours[day].closed}
                onValueChange={(open) =>
                  setHours({
                    ...hours,
                    [day]: { ...hours[day], open },
                  })
                }
              />
              <span className="text-xs text-muted-foreground">to</span>
              <TimePicker
                className="h-9 w-32"
                aria-label={`${DAY_LABELS[day]} close`}
                value={hours[day].close}
                disabled={hours[day].closed}
                onValueChange={(close) =>
                  setHours({
                    ...hours,
                    [day]: { ...hours[day], close },
                  })
                }
              />
            </div>
            <Label className="ml-auto flex items-center gap-2 text-xs text-muted-foreground">
              Closed
              <Switch
                checked={hours[day].closed}
                onCheckedChange={(checked) =>
                  setHours({
                    ...hours,
                    [day]: { ...hours[day], closed: checked },
                  })
                }
              />
            </Label>
          </div>
        ))}
      </div>
      <Button
        type="button"
        className="w-fit"
        onClick={submit}
        loading={saveHours.isPending}
      >
        Continue
      </Button>
    </div>
  );
}
