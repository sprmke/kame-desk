import { useEffect, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type DocumentTemplate } from "@/lib/apiClient";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import {
  DEFAULT_DOCUMENT_TEMPLATE_HTML,
  toEditorHtml,
} from "@/lib/documentTemplatePlaceholders";
import { DocumentTemplateEditor } from "@/features/documents/components/DocumentTemplateEditor";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field, FieldError } from "@/components/forms/Field";
import { FieldLabel } from "@/components/forms/FieldLabel";
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
import type { RichTextEditorHandle } from "@/components/ui/rich-text-editor";
import { Switch } from "@/components/ui/switch";

const TYPES = [
  "medical_certificate",
  "referral_letter",
  "lab_request",
  "confinement_certificate",
  "custom",
] as const;

export const TEMPLATE_TYPE_LABEL: Record<string, string> = {
  medical_certificate: "Medical certificate",
  referral_letter: "Referral letter",
  lab_request: "Lab request",
  confinement_certificate: "Confinement certificate",
  custom: "Custom",
};

type Props = {
  clinicId: string;
  /** `null` opens the modal in create mode. */
  template: DocumentTemplate | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function DocumentTemplateFormModal({
  clinicId,
  template,
  open,
  onOpenChange,
}: Props) {
  const qc = useQueryClient();
  const editorRef = useRef<RichTextEditorHandle>(null);
  const [name, setName] = useState("");
  const [key, setKey] = useState("");
  const [type, setType] = useState<string>("medical_certificate");
  const [active, setActive] = useState(true);
  const [body, setBody] = useState(DEFAULT_DOCUMENT_TEMPLATE_HTML);

  const editing = template !== null;

  // Load the selected template (or create-mode defaults) each time the modal
  // opens, so a cancelled edit never leaks into the next one.
  useEffect(() => {
    if (!open) return;
    if (template) {
      setName(template.name);
      setKey(template.template_key);
      setType(template.template_type);
      setActive(template.is_active);
      setBody(toEditorHtml(template.body_template ?? ""));
    } else {
      setName("");
      setKey("");
      setType("medical_certificate");
      setActive(true);
      setBody(DEFAULT_DOCUMENT_TEMPLATE_HTML);
    }
  }, [open, template]);

  function currentBody() {
    return editorRef.current?.getHTML() || body;
  }

  function onSaved() {
    qc.invalidateQueries({ queryKey: ["document-templates", clinicId] });
    onOpenChange(false);
  }

  const create = useMutation({
    mutationFn: () =>
      api.createDocumentTemplate(clinicId, {
        template_key: key.trim(),
        name: name.trim(),
        template_type: type,
        body_template: currentBody(),
        is_active: active,
      }),
    onSuccess: onSaved,
  });

  const update = useMutation({
    mutationFn: () =>
      api.patchDocumentTemplate(clinicId, template!.id, {
        name: name.trim(),
        body_template: currentBody(),
        is_active: active,
      }),
    onSuccess: onSaved,
  });

  const saving = create.isPending || update.isPending;
  const canSubmit =
    name.trim().length > 0 && (editing || key.trim().length > 0);

  return (
    <ResponsiveModal open={open} onOpenChange={onOpenChange}>
      <ResponsiveModalContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <ResponsiveModalHeader>
          <ResponsiveModalTitle>
            {editing ? "Edit template" : "New template"}
          </ResponsiveModalTitle>
        </ResponsiveModalHeader>
        <form
          className="flex flex-col gap-4"
          onSubmit={(e) => {
            e.preventDefault();
            if (!canSubmit || saving) return;
            if (editing) update.mutate();
            else create.mutate();
          }}
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <Field>
              <FieldLabel htmlFor="template-name" label="Name" required />
              <Input
                id="template-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={FORM_PLACEHOLDERS.templateName}
              />
            </Field>
            <Field>
              <FieldLabel htmlFor="template-key" label="Key" required />
              <Input
                id="template-key"
                value={key}
                onChange={(e) => setKey(e.target.value)}
                placeholder={FORM_PLACEHOLDERS.templateKey}
                disabled={editing}
              />
            </Field>
          </div>
          <Field>
            <FieldLabel htmlFor="template-type" label="Type" />
            <Select value={type} onValueChange={setType} disabled={editing}>
              <SelectTrigger id="template-type" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TYPES.map((t) => (
                  <SelectItem key={t} value={t}>
                    {TEMPLATE_TYPE_LABEL[t]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>

          <DocumentTemplateEditor
            content={body}
            onChange={setBody}
            editorRef={editorRef}
          />

          <FieldError>
            {create.error instanceof Error
              ? create.error.message
              : update.error instanceof Error
                ? update.error.message
                : null}
          </FieldError>

          <ResponsiveModalFooter className="items-center sm:justify-between">
            <label className="flex items-center gap-2 text-sm">
              <Switch
                checked={active}
                onCheckedChange={setActive}
                id="template-active"
              />
              Active
            </label>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={!canSubmit || saving}>
                {saving ? "Saving…" : "Save"}
              </Button>
            </div>
          </ResponsiveModalFooter>
        </form>
      </ResponsiveModalContent>
    </ResponsiveModal>
  );
}
