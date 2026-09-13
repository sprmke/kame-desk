import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
import { pageContainerClass } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  SettingsRow,
  SettingsSection,
} from "@/components/settings/SettingsSection";
import { Switch } from "@/components/ui/switch";

export function PlatformFlagsPage() {
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["platform-flag", "ai_assistant"],
    queryFn: () => api.getPlatformFlag("ai_assistant"),
  });
  const save = useMutation({
    mutationFn: (enabled: boolean) =>
      api.patchPlatformFlag("ai_assistant", enabled),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["platform-flag", "ai_assistant"] }),
  });

  return (
    <div className={pageContainerClass("narrow")}>
      <PageHeader title="Flags" />
      <SettingsSection>
        <SettingsRow label="AI assistant">
          <Switch
            id="ai-flag"
            checked={data?.enabled ?? false}
            onCheckedChange={(v) => save.mutate(v)}
            disabled={save.isPending}
          />
        </SettingsRow>
      </SettingsSection>
    </div>
  );
}
