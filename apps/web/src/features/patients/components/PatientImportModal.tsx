import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { FileUp } from "lucide-react";
import { api } from "@/lib/apiClient";
import { Button } from "@/components/ui/button";
import { FileDropzone } from "@/components/ui/file-dropzone";
import {
  ResponsiveModal,
  ResponsiveModalContent,
  ResponsiveModalFooter,
  ResponsiveModalHeader,
  ResponsiveModalTitle,
  ResponsiveModalTrigger,
} from "@/components/ui/responsive-modal";

const MAX_CSV_BYTES = 5 * 1024 * 1024;

type ImportResult = Awaited<ReturnType<typeof api.importPatients>>;

export function PatientImportModal() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [csvText, setCsvText] = useState("");
  const [fileError, setFileError] = useState<string | null>(null);
  const [preview, setPreview] = useState<ImportResult | null>(null);

  const previewImport = useMutation({
    mutationFn: (csv: string) => api.importPatients({ csv, commit: false }),
    onSuccess: setPreview,
  });

  const commitImport = useMutation({
    mutationFn: (csv: string) => api.importPatients({ csv, commit: true }),
    onSuccess: (result) => {
      setPreview(result);
      void queryClient.invalidateQueries({ queryKey: ["patients"] });
    },
  });

  function reset() {
    setFile(null);
    setCsvText("");
    setFileError(null);
    setPreview(null);
    previewImport.reset();
    commitImport.reset();
  }

  async function selectFile(nextFile: File | undefined) {
    if (!nextFile) return;
    const isCsv =
      nextFile.name.toLowerCase().endsWith(".csv") ||
      nextFile.type === "text/csv";
    if (!isCsv) {
      setFileError("Choose a CSV file.");
      return;
    }
    if (nextFile.size > MAX_CSV_BYTES) {
      setFileError("CSV must be 5 MB or smaller.");
      return;
    }

    setFile(nextFile);
    setFileError(null);
    setPreview(null);
    setCsvText(await nextFile.text());
  }

  const pending = previewImport.isPending || commitImport.isPending;
  const mutationError =
    previewImport.error instanceof Error
      ? previewImport.error.message
      : commitImport.error instanceof Error
        ? commitImport.error.message
        : null;

  return (
    <ResponsiveModal
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) reset();
      }}
    >
      <ResponsiveModalTrigger asChild>
        <Button type="button" variant="outline">
          <FileUp className="size-4" aria-hidden />
          Import
        </Button>
      </ResponsiveModalTrigger>
      <ResponsiveModalContent
        className="sm:max-w-xl"
        sheetBodyClassName="max-h-[92dvh]"
      >
        <ResponsiveModalHeader>
          <ResponsiveModalTitle>Import patients</ResponsiveModalTitle>
        </ResponsiveModalHeader>

        <div className="min-h-0 space-y-4 overflow-y-auto">
          <FileDropzone
            id="patient-import-csv"
            accept=".csv,text/csv"
            file={file}
            disabled={pending}
            error={fileError}
            hint="CSV, up to 5 MB"
            onFileSelect={(nextFile) => void selectFile(nextFile)}
            onClear={reset}
          />

          {preview ? (
            <div className="rounded-lg border border-border bg-muted/20 p-3 text-sm">
              <p className="font-medium text-foreground">
                {preview.items.length.toLocaleString()} rows
              </p>
              <p className="mt-1 text-muted-foreground">
                {preview.errors.length
                  ? `${preview.errors.length.toLocaleString()} errors`
                  : "Ready to import"}
                {preview.committed
                  ? ` · ${preview.created.toLocaleString()} created`
                  : ""}
              </p>
            </div>
          ) : null}

          {mutationError ? (
            <p className="text-sm text-destructive" role="alert">
              {mutationError}
            </p>
          ) : null}
        </div>

        <ResponsiveModalFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => setOpen(false)}
          >
            {preview?.committed ? "Done" : "Cancel"}
          </Button>
          {!preview?.committed ? (
            preview ? (
              <Button
                type="button"
                disabled={!csvText || pending || preview.errors.length > 0}
                onClick={() => commitImport.mutate(csvText)}
              >
                {commitImport.isPending ? "Importing…" : "Import"}
              </Button>
            ) : (
              <Button
                type="button"
                disabled={!csvText || pending}
                onClick={() => previewImport.mutate(csvText)}
              >
                {previewImport.isPending ? "Checking…" : "Preview"}
              </Button>
            )
          ) : null}
        </ResponsiveModalFooter>
      </ResponsiveModalContent>
    </ResponsiveModal>
  );
}
