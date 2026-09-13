import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const STATUS_VARIANT: Record<
  string,
  "default" | "brand" | "success" | "warning" | "error" | "info"
> = {
  active: "success",
  cancelled: "default",
  expired: "warning",
};

export function PatientMembershipCard({ patientId }: { patientId: string }) {
  const clinicId = getClinicId()!;
  const qc = useQueryClient();
  const [planId, setPlanId] = useState("");

  const { data: membership } = useQuery({
    queryKey: ["patient-membership", patientId],
    queryFn: () => api.getPatientMembership(patientId),
  });

  const { data: plans } = useQuery({
    queryKey: ["membership-plans", clinicId],
    queryFn: () => api.listMembershipPlans(clinicId),
  });

  const activePlans = (plans ?? []).filter((p) => p.is_active);

  const enroll = useMutation({
    mutationFn: () => api.enrollPatientMembership(patientId, planId),
    onSuccess: () => {
      setPlanId("");
      qc.invalidateQueries({ queryKey: ["patient-membership", patientId] });
    },
  });

  const cancel = useMutation({
    mutationFn: () => api.cancelPatientMembership(patientId, membership!.id),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["patient-membership", patientId] }),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Membership</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {membership ? (
          <div className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <span className="font-medium text-foreground">
                  {membership.plan_name ?? "Membership"}
                </span>
                <span className="ml-2 text-muted-foreground">
                  renews {membership.current_period_end}
                </span>
              </div>
              <Badge
                variant={STATUS_VARIANT[membership.status] ?? "default"}
                className="capitalize"
              >
                {membership.status}
              </Badge>
            </div>
            {Object.keys(membership.usage_this_period).length > 0 && (
              <p className="text-sm text-muted-foreground">
                Used this period:{" "}
                {Object.entries(membership.usage_this_period)
                  .map(([category, count]) => `${category} x${count}`)
                  .join(", ")}
              </p>
            )}
            {membership.status === "active" && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="w-fit text-destructive hover:text-destructive"
                disabled={cancel.isPending}
                onClick={() => cancel.mutate()}
              >
                Cancel membership
              </Button>
            )}
          </div>
        ) : activePlans.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No membership plans configured yet.
          </p>
        ) : (
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
            <Select value={planId} onValueChange={setPlanId}>
              <SelectTrigger className="w-full sm:w-64" aria-label="Plan">
                <SelectValue placeholder="Select a plan" />
              </SelectTrigger>
              <SelectContent>
                {activePlans.map((plan) => (
                  <SelectItem key={plan.id} value={plan.id}>
                    {plan.name} · PHP {plan.price}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              type="button"
              disabled={!planId || enroll.isPending}
              onClick={() => enroll.mutate()}
            >
              Enroll
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
