import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { FileText, Plus } from "lucide-react";
import { api, type DocumentTemplate } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import {
  DocumentTemplateFormModal,
  TEMPLATE_TYPE_LABEL,
} from "@/features/documents/components/DocumentTemplateFormModal";
import { SettingsSection } from "@/components/settings/SettingsSection";
import { Button } from "@/components/ui/button";
import { EmptyState, SectionCard } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { DocumentTemplatesSkeleton } from "@/components/skeletons/PageSkeletons";
import { EntityList, EntityRow } from "@/components/ui/entity-row";

export function DocumentTemplatesPage() {
  const clinicId = getClinicId();
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<DocumentTemplate | null>(null);

  const {
    data: templates,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["document-templates", clinicId],
    queryFn: () => api.listDocumentTemplates(clinicId!),
    enabled: Boolean(clinicId),
  });

  function openCreate() {
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(template: DocumentTemplate) {
    setEditing(template);
    setFormOpen(true);
  }

  const items = templates ?? [];

  return (
    <div>
      <SettingsSection
        title="Templates"
        divided={false}
        action={
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={openCreate}
          >
            <Plus className="size-4" />
            New template
          </Button>
        }
      >
        <SectionCard>
          {isLoading ? (
            <DocumentTemplatesSkeleton />
          ) : isError ? (
            <ErrorState onRetry={() => refetch()} />
          ) : items.length === 0 ? (
            <EmptyState
              icon={FileText}
              heading="No templates yet"
              size="sm"
              action={
                <Button type="button" onClick={openCreate}>
                  New template
                </Button>
              }
            />
          ) : (
            <EntityList>
              {items.map((t) => (
                <li key={t.id} className="px-2">
                  <button
                    type="button"
                    className="native-press w-full cursor-pointer rounded-lg px-1 text-left"
                    onClick={() => openEdit(t)}
                  >
                    <EntityRow
                      title={t.name}
                      subtitle={`${TEMPLATE_TYPE_LABEL[t.template_type] ?? t.template_type} · ${t.template_key}${t.is_active ? "" : " · Inactive"}`}
                    />
                  </button>
                </li>
              ))}
            </EntityList>
          )}
        </SectionCard>
      </SettingsSection>

      {clinicId ? (
        <DocumentTemplateFormModal
          clinicId={clinicId}
          template={editing}
          open={formOpen}
          onOpenChange={setFormOpen}
        />
      ) : null}
    </div>
  );
}
