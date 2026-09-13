import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getClinicId } from "@/lib/auth";
import { api } from "@/lib/apiClient";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  SettingsRow,
  SettingsSection,
} from "@/components/settings/SettingsSection";
import { Switch } from "@/components/ui/switch";
import { AssistantSettingsSkeleton } from "@/components/skeletons/PageSkeletons";

const TOOL_TOGGLES = [
  { key: "propose_book_appointment", label: "Book appointments" },
  { key: "propose_reschedule_appointment", label: "Reschedule" },
  { key: "propose_cancel_appointment", label: "Cancel appointments" },
  { key: "propose_send_reminder", label: "Send reminders" },
  { key: "propose_save_soap_note", label: "Draft SOAP notes" },
] as const;

export function AssistantSettingsPage() {
  const clinicId = getClinicId();
  const qc = useQueryClient();
  const { data: clinic, isLoading } = useQuery({
    queryKey: ["clinic", clinicId],
    queryFn: () => api.getClinic(clinicId!),
    enabled: !!clinicId,
  });
  const { data: usage } = useQuery({
    queryKey: ["assistant-usage", clinicId],
    queryFn: () => api.getAssistantUsage(),
    enabled: !!clinicId,
  });

  const save = useMutation({
    mutationFn: (body: {
      ai_assistant_enabled?: boolean;
      assistant_disabled_tools?: string[];
    }) => api.patchClinic(clinicId!, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["clinic", clinicId] }),
  });

  if (!clinicId) {
    return (
      <div className="w-full">
        <PageHeader title="Assistant" />
        <p className="text-sm text-muted-foreground">Select a clinic first.</p>
      </div>
    );
  }

  const disabled = new Set(clinic?.assistant_disabled_tools ?? []);

  return (
    <div className="w-full">
      <PageHeader title="Assistant" />
      {isLoading || !clinic ? (
        <AssistantSettingsSkeleton />
      ) : (
        <SettingsSection>
          <SettingsRow label="Enable clinic assistant">
            <Switch
              id="assistant-enabled"
              checked={clinic.ai_assistant_enabled ?? false}
              onCheckedChange={(v) => save.mutate({ ai_assistant_enabled: v })}
              disabled={save.isPending}
            />
          </SettingsRow>
          {TOOL_TOGGLES.map((tool) => (
            <SettingsRow key={tool.key} label={tool.label}>
              <Switch
                id={tool.key}
                checked={!disabled.has(tool.key)}
                onCheckedChange={(on) => {
                  const next = new Set(disabled);
                  if (on) next.delete(tool.key);
                  else next.add(tool.key);
                  save.mutate({
                    assistant_disabled_tools: Array.from(next),
                  });
                }}
                disabled={save.isPending}
              />
            </SettingsRow>
          ))}
        </SettingsSection>
      )}
      {usage ? (
        <SettingsSection title="Usage (30 days)">
          <SettingsRow
            label={`${usage.request_total} requests`}
            description={`Daily cap ${usage.daily_cap}`}
          />
        </SettingsSection>
      ) : null}
    </div>
  );
}
