import { Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { ChevronLeft, FileText } from "lucide-react";
import { api, type GeneratedDocument } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { toEditorHtml } from "@/lib/documentTemplatePlaceholders";
import { pageContainerClass } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RichTextDisplay } from "@/components/ui/rich-text-editor";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type Props = { patientId: string };

export function DocumentNewPage({ patientId }: Props) {
  const clinicId = getClinicId();
  const navigate = useNavigate();
  const [draft, setDraft] = useState<GeneratedDocument | null>(null);
  const [recipient, setRecipient] = useState("");
  const [pendingTemplateId, setPendingTemplateId] = useState<string | null>(
    null,
  );

  const { data: patient } = useQuery({
    queryKey: ["patient", patientId],
    queryFn: () => api.getPatient(patientId),
  });

  const { data: templates } = useQuery({
    queryKey: ["document-templates", clinicId],
    queryFn: () => api.listDocumentTemplates(clinicId!),
    enabled: Boolean(clinicId),
  });

  const pendingTemplate = templates?.find((t) => t.id === pendingTemplateId);

  const create = useMutation({
    mutationFn: (args: { templateId: string; referralRecipient?: string }) =>
      api.createDocumentDraft(patientId, {
        template_id: args.templateId,
        referral_recipient: args.referralRecipient,
      }),
    onSuccess: (doc) => {
      setDraft(doc);
      setPendingTemplateId(null);
    },
  });

  const saveReferral = useMutation({
    mutationFn: (body: {
      referral_recipient?: string;
      referral_status?: string;
      referral_outcome?: string;
    }) => api.patchDocument(draft!.id, body),
    onSuccess: (doc) => setDraft(doc),
  });

  const issue = useMutation({
    mutationFn: () => api.issueDocument(draft!.id),
    onSuccess: () =>
      navigate({ to: "/dashboard/patients/$patientId", params: { patientId } }),
  });

  function pickTemplate(templateId: string) {
    const template = templates?.find((t) => t.id === templateId);
    if (template?.template_type === "referral_letter") {
      setPendingTemplateId(templateId);
      return;
    }
    create.mutate({ templateId });
  }

  return (
    <div className={pageContainerClass("narrow")}>
      <Link
        to="/dashboard/patients/$patientId"
        params={{ patientId }}
        className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ChevronLeft className="size-4" />
        {patient?.full_name ?? "Patient"}
      </Link>
      <PageHeader title="Generate document" />

      {!draft && pendingTemplate ? (
        <Card>
          <CardContent className="flex flex-col gap-3 pt-5">
            <p className="text-sm font-medium">{pendingTemplate.name}</p>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="referral-to">Recipient</Label>
              <Input
                id="referral-to"
                value={recipient}
                onChange={(e) => setRecipient(e.target.value)}
                placeholder={FORM_PLACEHOLDERS.referralRecipient}
              />
            </div>
            <div className="flex gap-2">
              <Button
                type="button"
                disabled={create.isPending || !recipient.trim()}
                onClick={() =>
                  create.mutate({
                    templateId: pendingTemplate.id,
                    referralRecipient: recipient.trim(),
                  })
                }
              >
                Draft
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setPendingTemplateId(null)}
              >
                Back
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : !draft ? (
        <Card>
          <CardContent className="flex flex-col gap-2 pt-5">
            {(templates ?? [])
              .filter((t) => t.is_active)
              .map((t) => (
                <Button
                  key={t.id}
                  type="button"
                  variant="outline"
                  className="justify-start"
                  disabled={create.isPending}
                  onClick={() => pickTemplate(t.id)}
                >
                  <FileText className="size-4" />
                  {t.name}
                </Button>
              ))}
          </CardContent>
        </Card>
      ) : (
        <div className="flex flex-col gap-4">
          {draft.document_type === "referral_letter" && (
            <Card>
              <CardContent className="flex flex-col gap-3 pt-5">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="ref-status">Referral status</Label>
                  <Select
                    value={draft.referral_status ?? "draft"}
                    onValueChange={(value) =>
                      saveReferral.mutate({ referral_status: value })
                    }
                  >
                    <SelectTrigger id="ref-status">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="draft">Draft</SelectItem>
                      <SelectItem value="sent">Sent</SelectItem>
                      <SelectItem value="acknowledged">Acknowledged</SelectItem>
                      <SelectItem value="completed">Completed</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="ref-outcome">Outcome</Label>
                  <Input
                    id="ref-outcome"
                    defaultValue={draft.referral_outcome ?? ""}
                    onBlur={(e) => {
                      const value = e.target.value.trim();
                      if (value === (draft.referral_outcome ?? "")) return;
                      saveReferral.mutate({
                        referral_outcome: value || undefined,
                      });
                    }}
                  />
                </div>
                {draft.referral_recipient ? (
                  <p className="text-sm text-muted-foreground">
                    To {draft.referral_recipient}
                  </p>
                ) : null}
              </CardContent>
            </Card>
          )}
          <Card>
            <CardContent className="pt-5">
              <div className="overflow-hidden rounded-lg border border-border">
                <RichTextDisplay
                  content={toEditorHtml(draft.preview_content)}
                />
              </div>
            </CardContent>
          </Card>
          <div className="flex gap-2">
            <Button
              type="button"
              disabled={issue.isPending}
              onClick={() => issue.mutate()}
            >
              {issue.isPending ? "Issuing…" : "Issue"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setDraft(null)}
            >
              Back
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
