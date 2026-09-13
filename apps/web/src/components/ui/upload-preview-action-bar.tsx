import { Upload, X } from "lucide-react";

type Props = {
  inputId: string;
  onRemove: () => void;
  replaceLabel?: string;
};

export function UploadPreviewActionBar({
  inputId,
  onRemove,
  replaceLabel = "Replace",
}: Props) {
  return (
    <div className="absolute inset-0 flex items-end justify-between gap-2 bg-gradient-to-t from-black/55 to-transparent p-2">
      <label
        htmlFor={inputId}
        className="inline-flex min-h-11 cursor-pointer items-center gap-1.5 rounded-lg bg-background/95 px-3 text-xs font-medium text-foreground"
      >
        <Upload className="size-3.5" aria-hidden />
        {replaceLabel}
      </label>
      <button
        type="button"
        onClick={onRemove}
        className="inline-flex size-11 items-center justify-center rounded-lg bg-background/95 text-foreground"
        aria-label="Remove file"
      >
        <X className="size-4" />
      </button>
    </div>
  );
}
