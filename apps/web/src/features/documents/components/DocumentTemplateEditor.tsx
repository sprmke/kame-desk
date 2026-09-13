import { useCallback, useRef, useState } from "react";
import { Eye, Pencil } from "lucide-react";
import { Field } from "@/components/forms/Field";
import { FieldLabel } from "@/components/forms/FieldLabel";
import { SegmentedControl } from "@/components/ui/sliding-tabs";
import {
  RichTextDisplay,
  RichTextEditor,
  type RichTextEditorHandle,
} from "@/components/ui/rich-text-editor";
import {
  PlaceholdersButton,
  TemplatePlaceholdersDialog,
} from "@/components/ui/template-placeholders";
import {
  applyDocumentTemplatePlaceholders,
  DOCUMENT_PLACEHOLDER_KEY_SET,
} from "@/lib/documentTemplatePlaceholders";
import { cn } from "@/lib/utils";

type EditorTab = "edit" | "preview";

const EDITOR_VIEW_OPTIONS = [
  {
    value: "edit" as const,
    label: <span className="hidden sm:inline">Edit</span>,
    ariaLabel: "Edit",
    icon: Pencil,
  },
  {
    value: "preview" as const,
    label: <span className="hidden sm:inline">Preview</span>,
    ariaLabel: "Preview",
    icon: Eye,
  },
];

type DocumentTemplateEditorProps = {
  content: string;
  onChange: (content: string) => void;
  editorRef?: React.RefObject<RichTextEditorHandle | null>;
  className?: string;
};

export function DocumentTemplateEditor({
  content,
  onChange,
  editorRef: externalRef,
  className,
}: DocumentTemplateEditorProps) {
  const internalRef = useRef<RichTextEditorHandle>(null);
  const editorRef = externalRef ?? internalRef;
  const [tab, setTab] = useState<EditorTab>("edit");
  const [placeholdersOpen, setPlaceholdersOpen] = useState(false);
  const [previewHtml, setPreviewHtml] = useState("");

  const handleTabChange = useCallback(
    (next: EditorTab) => {
      if (next === "preview") {
        setPreviewHtml(
          applyDocumentTemplatePlaceholders(
            editorRef.current?.getHTML() || content,
          ),
        );
      }
      setTab(next);
    },
    [content, editorRef],
  );

  const insertToken = useCallback(
    (token: string) => {
      if (tab !== "edit") setTab("edit");
      window.setTimeout(() => {
        editorRef.current?.insertToken(token);
      }, 0);
    },
    [tab, editorRef],
  );

  return (
    <Field className={className}>
      <FieldLabel label="Body" required />

      <div className="overflow-hidden rounded-lg border border-border bg-card">
        <div className="flex flex-nowrap items-center justify-between gap-1.5 border-b px-2.5 py-1.5 sm:gap-2 sm:px-4 sm:py-2">
          <SegmentedControl
            size="dense"
            value={tab}
            onChange={handleTabChange}
            aria-label="Template editor view"
            options={EDITOR_VIEW_OPTIONS}
            listClassName="shrink-0"
            triggerClassName="px-2 sm:px-2.5"
          />
          {tab === "edit" ? (
            <PlaceholdersButton onClick={() => setPlaceholdersOpen(true)} />
          ) : (
            <div className="size-8 shrink-0 sm:size-auto" aria-hidden />
          )}
        </div>

        <div className="min-w-0">
          <div
            className={cn(tab !== "edit" && "hidden")}
            inert={tab !== "edit" || undefined}
          >
            <RichTextEditor
              ref={editorRef}
              content={content}
              onChange={onChange}
              validPlaceholderKeys={DOCUMENT_PLACEHOLDER_KEY_SET}
              className="border-0 rounded-none shadow-none"
              minHeight="280px"
            />
          </div>
          <div
            className={cn("bg-card", tab !== "preview" && "hidden")}
            inert={tab !== "preview" || undefined}
          >
            <RichTextDisplay content={previewHtml} className="min-h-[280px]" />
          </div>
        </div>
      </div>

      <TemplatePlaceholdersDialog
        open={placeholdersOpen}
        onOpenChange={setPlaceholdersOpen}
        onInsert={insertToken}
      />
    </Field>
  );
}
