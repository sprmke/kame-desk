import * as React from "react";
import {
  FileSpreadsheet,
  FileText,
  ImagePlus,
  Loader2,
  Upload,
  X,
  type LucideIcon,
} from "lucide-react";
import { UploadPreviewActionBar } from "@/components/ui/upload-preview-action-bar";
import { cn } from "@/lib/utils";

function useFileDragState(disabled: boolean) {
  const [isDragging, setIsDragging] = React.useState(false);
  const dragDepth = React.useRef(0);

  const handlers = React.useMemo(
    () => ({
      onDragEnter: (e: React.DragEvent) => {
        if (disabled) return;
        e.preventDefault();
        e.stopPropagation();
        dragDepth.current += 1;
        setIsDragging(true);
      },
      onDragLeave: (e: React.DragEvent) => {
        if (disabled) return;
        e.preventDefault();
        e.stopPropagation();
        dragDepth.current = Math.max(0, dragDepth.current - 1);
        if (dragDepth.current === 0) setIsDragging(false);
      },
      onDragOver: (e: React.DragEvent) => {
        if (disabled) return;
        e.preventDefault();
        e.stopPropagation();
      },
      onDrop: (
        e: React.DragEvent,
        onFile: (file: File | undefined) => void,
      ) => {
        if (disabled) return;
        e.preventDefault();
        e.stopPropagation();
        dragDepth.current = 0;
        setIsDragging(false);
        const file = e.dataTransfer.files?.[0];
        onFile(file);
      },
    }),
    [disabled],
  );

  return { isDragging, handlers };
}

type ImageDropzoneProps = {
  id: string;
  accept?: string;
  imageUrl: string | null;
  uploading?: boolean;
  disabled?: boolean;
  emptyLabel?: string;
  emptyIcon?: LucideIcon;
  onFileSelect: (file: File | undefined) => void;
  onRemove: () => void;
};

export function ImageFileDropzone({
  id,
  accept = "image/jpeg,image/png,image/webp",
  imageUrl,
  uploading = false,
  disabled = false,
  emptyLabel = "Upload",
  emptyIcon: EmptyIcon = ImagePlus,
  onFileSelect,
  onRemove,
}: ImageDropzoneProps) {
  const busy = disabled || uploading;
  const hasImage = Boolean(imageUrl?.trim());
  const { isDragging, handlers } = useFileDragState(busy);

  return (
    <div
      className={cn(
        "relative flex min-h-[140px] items-center justify-center overflow-hidden rounded-xl border border-dashed border-border bg-muted/20 transition-shadow",
        busy && !uploading && "opacity-60",
        isDragging &&
          "ring-2 ring-primary ring-offset-2 ring-offset-background",
      )}
      {...handlers}
      onDrop={(e) => handlers.onDrop(e, onFileSelect)}
    >
      {uploading ? (
        <div className="flex flex-col items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="size-5 animate-spin" aria-hidden />
          Uploading
        </div>
      ) : hasImage ? (
        <>
          <img
            src={imageUrl!}
            alt=""
            className="absolute inset-0 size-full object-contain p-3"
          />
          <UploadPreviewActionBar inputId={id} onRemove={onRemove} />
        </>
      ) : (
        <label
          htmlFor={id}
          className={cn(
            "flex min-h-[140px] w-full cursor-pointer flex-col items-center justify-center gap-2 px-4 py-6 text-center",
            !busy && "hover:bg-muted/30",
            busy && "cursor-not-allowed",
          )}
        >
          <span className="flex size-10 items-center justify-center rounded-full bg-primary/10 text-primary">
            <EmptyIcon className="size-5" aria-hidden />
          </span>
          <span className="text-sm font-medium text-foreground">
            {emptyLabel}
          </span>
        </label>
      )}
      <input
        id={id}
        type="file"
        accept={accept}
        className="sr-only"
        disabled={busy}
        onChange={(e) => {
          onFileSelect(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
    </div>
  );
}

type DocumentDropzoneProps = {
  id: string;
  accept: string;
  file: File | null;
  previewUrl: string | null;
  uploading?: boolean;
  hasError?: boolean;
  emptyLabel?: string;
  emptyHint?: string;
  onFileSelect: (file: File | undefined) => void;
  onClear: () => void;
};

function isPdfFile(file: File | null, previewUrl: string | null) {
  return (
    file?.type === "application/pdf" ||
    (previewUrl?.toLowerCase().includes(".pdf") ?? false) ||
    (file?.name.toLowerCase().endsWith(".pdf") ?? false)
  );
}

export function DocumentFileDropzone({
  id,
  accept,
  file,
  previewUrl,
  uploading = false,
  hasError = false,
  emptyLabel = "Upload",
  emptyHint,
  onFileSelect,
  onClear,
}: DocumentDropzoneProps) {
  const isPdf = isPdfFile(file, previewUrl);
  const hasImagePreview = Boolean(previewUrl && !isPdf);
  const hasDocument = Boolean(file || previewUrl);
  const { isDragging, handlers } = useFileDragState(uploading);

  return (
    <div
      className={cn(
        "relative flex min-h-[140px] items-center justify-center overflow-hidden rounded-xl border border-dashed border-border bg-muted/20 transition-shadow",
        hasError && "border-destructive",
        uploading && "opacity-70",
        isDragging &&
          "ring-2 ring-primary ring-offset-2 ring-offset-background",
      )}
      {...handlers}
      onDrop={(e) => handlers.onDrop(e, onFileSelect)}
    >
      {uploading ? (
        <div className="flex flex-col items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="size-5 animate-spin" aria-hidden />
          Uploading
        </div>
      ) : hasImagePreview ? (
        <>
          <img
            src={previewUrl!}
            alt=""
            className="absolute inset-0 size-full object-cover"
          />
          <UploadPreviewActionBar inputId={id} onRemove={onClear} />
        </>
      ) : hasDocument ? (
        <>
          <div className="flex w-full flex-col items-center gap-2 px-4 py-6">
            <FileText className="size-8 text-primary" aria-hidden />
            <p className="max-w-full truncate text-sm font-medium text-foreground">
              {file?.name ?? "Document uploaded"}
            </p>
          </div>
          <UploadPreviewActionBar inputId={id} onRemove={onClear} />
        </>
      ) : (
        <label
          htmlFor={id}
          className="flex min-h-[140px] w-full cursor-pointer flex-col items-center justify-center gap-2 px-4 py-6 text-center hover:bg-muted/30"
        >
          <span className="flex size-10 items-center justify-center rounded-full bg-primary/10 text-primary">
            <ImagePlus className="size-5" aria-hidden />
          </span>
          <span className="text-sm font-medium text-foreground">
            {emptyLabel}
          </span>
          {emptyHint ? (
            <span className="text-xs text-muted-foreground">{emptyHint}</span>
          ) : null}
        </label>
      )}
      <input
        id={id}
        type="file"
        accept={accept}
        className="sr-only"
        onChange={(e) => {
          onFileSelect(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
    </div>
  );
}

type FileDropzoneProps = {
  id: string;
  accept: string;
  file: File | null;
  disabled?: boolean;
  error?: string | null;
  hint?: string;
  onFileSelect: (file: File | undefined) => void;
  onClear: () => void;
};

export function FileDropzone({
  id,
  accept,
  file,
  disabled = false,
  error,
  hint,
  onFileSelect,
  onClear,
}: FileDropzoneProps) {
  const inputRef = React.useRef<HTMLInputElement>(null);
  const { isDragging, handlers } = useFileDragState(disabled);

  return (
    <div className="space-y-2">
      <input
        ref={inputRef}
        id={id}
        type="file"
        accept={accept}
        className="peer sr-only"
        disabled={disabled}
        onChange={(event) => {
          onFileSelect(event.target.files?.[0]);
          event.target.value = "";
        }}
      />
      <div
        className={cn(
          "relative flex min-h-[180px] items-center justify-center overflow-hidden rounded-xl border border-dashed border-border bg-muted/20 transition-colors peer-focus-visible:ring-2 peer-focus-visible:ring-ring peer-focus-visible:ring-offset-2 motion-reduce:transition-none",
          !disabled &&
            !file &&
            "hover:border-primary/50 hover:bg-primary/[0.03]",
          isDragging && "border-primary bg-primary/5",
          error && "border-destructive",
          disabled && "opacity-70",
        )}
        {...handlers}
        onDrop={(event) => handlers.onDrop(event, onFileSelect)}
      >
        {file ? (
          <div className="flex w-full flex-col items-center gap-2 px-4 py-8 text-center">
            <span className="flex size-11 items-center justify-center rounded-full bg-primary/10 text-primary">
              <FileSpreadsheet className="size-5" aria-hidden />
            </span>
            <p className="max-w-full truncate text-sm font-medium text-foreground">
              {file.name}
            </p>
            <p className="text-xs tabular-nums text-muted-foreground">
              {Math.max(1, Math.ceil(file.size / 1024)).toLocaleString()} KB
            </p>
            <div className="mt-1 flex gap-2">
              <label
                htmlFor={id}
                className="inline-flex min-h-11 cursor-pointer items-center rounded-lg border border-border bg-background px-3 text-sm font-medium"
              >
                Replace
              </label>
              <button
                type="button"
                onClick={() => {
                  onClear();
                  if (inputRef.current) inputRef.current.value = "";
                }}
                className="inline-flex min-h-11 cursor-pointer items-center gap-1.5 rounded-lg px-3 text-sm font-medium text-muted-foreground hover:bg-muted"
              >
                <X className="size-4" aria-hidden />
                Remove
              </button>
            </div>
          </div>
        ) : (
          <label
            htmlFor={id}
            className={cn(
              "flex min-h-[180px] w-full flex-col items-center justify-center gap-2.5 px-4 py-8 text-center",
              disabled ? "cursor-not-allowed" : "cursor-pointer",
            )}
          >
            <span className="flex size-11 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Upload className="size-5" aria-hidden />
            </span>
            <span className="text-sm font-medium text-foreground">
              Drop a CSV here or browse
            </span>
            {hint ? (
              <span className="text-xs text-muted-foreground">{hint}</span>
            ) : null}
          </label>
        )}
      </div>
      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
