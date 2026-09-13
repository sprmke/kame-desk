import { useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
import { saveSupportSession } from "@/lib/auth";
import { pageContainerClass } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function PlatformTenantDetailPage({ clinicId }: { clinicId: string }) {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const orgId = clinicId;

  const { data: tenant } = useQuery({
    queryKey: ["platform-tenant", orgId],
    queryFn: () => api.getPlatformTenant(orgId),
  });

  const patch = useMutation({
    mutationFn: (body: { status?: string; plan_key?: string }) =>
      api.patchPlatformTenant(orgId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["platform-tenants"] });
      qc.invalidateQueries({ queryKey: ["platform-tenant", orgId] });
    },
  });

  const patchEnrollment = useMutation({
    mutationFn: (args: { clinicId: string; status: string }) =>
      api.patchPlatformEnrollment(orgId, args.clinicId, {
        status: args.status,
      }),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["platform-tenant", orgId] }),
  });

  const impersonate = useMutation({
    mutationFn: () => api.impersonateTenant(orgId),
    onSuccess: (res) => {
      saveSupportSession(res.access_token, res.clinic_id);
      window.location.assign("/dashboard");
    },
  });

  return (
    <div className={pageContainerClass("narrow")}>
      <Button
        variant="ghost"
        size="sm"
        className="mb-3"
        onClick={() => navigate({ to: "/platform" })}
      >
        Back
      </Button>
      <PageHeader title={tenant?.name ?? "Organization"} />
      <Card>
        <CardContent className="flex flex-col gap-4 pt-5 text-sm">
          <p className="text-muted-foreground">
            {tenant?.status} · {tenant?.plan_key}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              disabled={patch.isPending}
              onClick={() =>
                patch.mutate({
                  status:
                    tenant?.status === "suspended" ? "active" : "suspended",
                })
              }
            >
              {tenant?.status === "suspended" ? "Reactivate" : "Suspend"}
            </Button>
            {(["starter", "pro", "clinic"] as const).map((plan) => (
              <Button
                key={plan}
                type="button"
                variant={tenant?.plan_key === plan ? "default" : "outline"}
                disabled={patch.isPending}
                onClick={() => patch.mutate({ plan_key: plan })}
              >
                {plan}
              </Button>
            ))}
          </div>

          {tenant?.enrollments?.length ? (
            <ul className="space-y-2">
              {tenant.enrollments.map((row) => (
                <li
                  key={row.clinic_id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-border px-3 py-2"
                >
                  <div>
                    <p className="font-medium">{row.clinic_name}</p>
                    <Badge
                      variant={
                        row.status === "active" ? "default" : "secondary"
                      }
                    >
                      {row.status}
                    </Badge>
                  </div>
                  {row.status === "pending_enrollment" ? (
                    <Button
                      type="button"
                      size="sm"
                      disabled={patchEnrollment.isPending}
                      onClick={() =>
                        patchEnrollment.mutate({
                          clinicId: row.clinic_id,
                          status: "active",
                        })
                      }
                    >
                      Activate
                    </Button>
                  ) : row.status === "active" ? (
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      disabled={patchEnrollment.isPending}
                      onClick={() =>
                        patchEnrollment.mutate({
                          clinicId: row.clinic_id,
                          status: "deactivated",
                        })
                      }
                    >
                      Deactivate
                    </Button>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : null}

          <Button
            type="button"
            disabled={impersonate.isPending}
            onClick={() => impersonate.mutate()}
          >
            Support login
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
