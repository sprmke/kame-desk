import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, X } from "lucide-react";
import {
  api,
  type MembershipBillingInterval,
  type MembershipIncludedService,
  type MembershipPlan,
} from "@/lib/apiClient";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field, FieldError } from "@/components/forms/Field";
import { FieldLabel } from "@/components/forms/FieldLabel";
import { Switch } from "@/components/ui/switch";
import {
  ResponsiveModal,
  ResponsiveModalContent,
  ResponsiveModalFooter,
  ResponsiveModalHeader,
  ResponsiveModalTitle,
} from "@/components/ui/responsive-modal";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const INTERVALS: MembershipBillingInterval[] = [
  "monthly",
  "quarterly",
  "annual",
];

const INTERVAL_LABEL: Record<MembershipBillingInterval, string> = {
  monthly: "Monthly",
  quarterly: "Quarterly",
  annual: "Annual",
};

type Props = {
  clinicId: string;
  /** `null` opens the modal in create mode. */
  plan: MembershipPlan | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function MembershipPlanFormModal({
  clinicId,
  plan,
  open,
  onOpenChange,
}: Props) {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [interval, setInterval] =
    useState<MembershipBillingInterval>("monthly");
  const [active, setActive] = useState(true);
  const [services, setServices] = useState<MembershipIncludedService[]>([]);

  const editing = plan !== null;

  useEffect(() => {
    if (!open) return;
    if (plan) {
      setName(plan.name);
      setPrice(plan.price);
      setInterval(plan.billing_interval);
      setActive(plan.is_active);
      setServices(plan.included_services);
    } else {
      setName("");
      setPrice("");
      setInterval("monthly");
      setActive(true);
      setServices([]);
    }
  }, [open, plan]);

  const save = useMutation({
    mutationFn: () => {
      const body = {
        name: name.trim(),
        price,
        billing_interval: interval,
        included_services: services.filter((s) => s.category.trim()),
      };
      if (editing) {
        return api.updateMembershipPlan(clinicId, plan.id, {
          ...body,
          is_active: active,
        });
      }
      return api.createMembershipPlan(clinicId, body);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["membership-plans", clinicId] });
      onOpenChange(false);
    },
  });

  const canSubmit = name.trim().length > 0 && price.trim().length > 0;

  function addService() {
    setServices((prev) => [...prev, { category: "", count_per_period: 1 }]);
  }

  function updateService(
    index: number,
    next: Partial<MembershipIncludedService>,
  ) {
    setServices((prev) =>
      prev.map((s, i) => (i === index ? { ...s, ...next } : s)),
    );
  }

  function removeService(index: number) {
    setServices((prev) => prev.filter((_, i) => i !== index));
  }

  return (
    <ResponsiveModal open={open} onOpenChange={onOpenChange}>
      <ResponsiveModalContent className="max-w-md">
        <ResponsiveModalHeader>
          <ResponsiveModalTitle>
            {editing ? "Edit membership plan" : "New membership plan"}
          </ResponsiveModalTitle>
        </ResponsiveModalHeader>
        <form
          className="flex flex-col gap-4"
          onSubmit={(e) => {
            e.preventDefault();
            if (!canSubmit || save.isPending) return;
            save.mutate();
          }}
        >
          <Field>
            <FieldLabel htmlFor="plan-name" label="Name" required />
            <Input
              id="plan-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Wellness membership"
            />
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field>
              <FieldLabel htmlFor="plan-price" label="Price" required />
              <Input
                id="plan-price"
                type="number"
                min={0}
                step="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="0.00"
              />
            </Field>
            <Field>
              <FieldLabel htmlFor="plan-interval" label="Billing interval" />
              <Select
                value={interval}
                onValueChange={(v) =>
                  setInterval(v as MembershipBillingInterval)
                }
              >
                <SelectTrigger id="plan-interval">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {INTERVALS.map((i) => (
                    <SelectItem key={i} value={i}>
                      {INTERVAL_LABEL[i]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
          </div>

          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <FieldLabel label="Included services" />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addService}
              >
                <Plus className="size-3.5" />
                Add
              </Button>
            </div>
            {services.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No allowances — this plan waives nothing automatically.
              </p>
            ) : (
              <div className="flex flex-col gap-2">
                {services.map((service, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <Input
                      value={service.category}
                      onChange={(e) =>
                        updateService(index, { category: e.target.value })
                      }
                      placeholder="Category (e.g. consultation)"
                      className="flex-1"
                    />
                    <Input
                      type="number"
                      min={1}
                      value={service.count_per_period}
                      onChange={(e) =>
                        updateService(index, {
                          count_per_period: Number(e.target.value) || 1,
                        })
                      }
                      className="w-20"
                      aria-label="Count per period"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground hover:text-destructive"
                      onClick={() => removeService(index)}
                      aria-label="Remove"
                    >
                      <X className="size-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {editing && (
            <div className="flex items-center justify-between rounded-md border border-border p-3">
              <FieldLabel label="Active" />
              <Switch checked={active} onCheckedChange={setActive} />
            </div>
          )}

          <FieldError>
            {save.isError ? "Could not save the plan." : null}
          </FieldError>
          <ResponsiveModalFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!canSubmit || save.isPending}>
              {save.isPending ? "Saving…" : "Save"}
            </Button>
          </ResponsiveModalFooter>
        </form>
      </ResponsiveModalContent>
    </ResponsiveModal>
  );
}
