import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { api } from "@/lib/apiClient";
import { clearAuth, getClinicId } from "@/lib/auth";
import { useSession } from "@/hooks/useSession";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  SettingsRow,
  SettingsSection,
} from "@/components/settings/SettingsSection";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

function formatWhen(iso: string) {
  return new Date(iso).toLocaleString("en-PH", {
    timeZone: "Asia/Manila",
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function AccountSettingsPage() {
  const clinicId = getClinicId()!;
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { can } = useSession();
  const { data: sessions } = useQuery({
    queryKey: ["sessions"],
    queryFn: () => api.listSessions(),
  });
  const { data: clinic } = useQuery({
    queryKey: ["clinic", clinicId],
    queryFn: () => api.getClinic(clinicId),
  });

  const canExport = can("settings:export");
  const isOwner = can("settings:delete_clinic");

  const logoutAll = useMutation({
    mutationFn: () => api.logoutEverywhere(),
    onSuccess: () => {
      clearAuth();
      navigate({ to: "/login" });
    },
  });

  const requestDeletion = useMutation({
    mutationFn: () => api.requestClinicDeletion(clinicId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["clinic", clinicId] }),
  });

  return (
    <div>
      <PageHeader title="Account" />

      <SettingsSection title="Sessions">
        {(sessions ?? []).map((s) => (
          <SettingsRow
            key={s.id}
            label={formatWhen(s.created_at)}
            description={`Expires ${formatWhen(s.expires_at)}`}
          />
        ))}
        <SettingsRow label="All devices">
          <Button
            type="button"
            variant="outline"
            onClick={() => logoutAll.mutate()}
            disabled={logoutAll.isPending}
          >
            Sign out everywhere
          </Button>
        </SettingsRow>
      </SettingsSection>

      {canExport ? (
        <SettingsSection title="Export">
          <SettingsRow label="Patients">
            <Button
              type="button"
              variant="outline"
              onClick={() => api.downloadPatientsCsv(clinicId)}
            >
              CSV
            </Button>
          </SettingsRow>
          <SettingsRow label="Appointments">
            <Button
              type="button"
              variant="outline"
              onClick={() => api.downloadAppointmentsCsv(clinicId)}
            >
              CSV
            </Button>
          </SettingsRow>
        </SettingsSection>
      ) : null}

      {isOwner ? (
        <SettingsSection title="Clinic deletion">
          <SettingsRow
            label="Request deletion"
            description={
              clinic?.deletion_requested_at
                ? `Requested ${formatWhen(clinic.deletion_requested_at)}.`
                : "Files a request. Patient data is not erased immediately."
            }
          >
            {clinic?.deletion_requested_at ? null : (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button type="button" variant="destructive">
                    Request deletion
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>
                      Request clinic deletion?
                    </AlertDialogTitle>
                    <AlertDialogDescription>
                      This files a deletion request. Patient data is not erased
                      immediately.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={() => requestDeletion.mutate()}>
                      Confirm
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </SettingsRow>
        </SettingsSection>
      ) : null}
    </div>
  );
}
