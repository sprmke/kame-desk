import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { SpecialtySelect } from "./SpecialtySelect";
import { doctorProfileSchema, type DoctorProfileValues } from "../lib/schemas";
import { useOnboardingMutations } from "../hooks/useOnboarding";
import { api } from "@/lib/apiClient";
import { Button } from "@/components/ui/button";
import { ImageFileDropzone } from "@/components/ui/file-dropzone";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Props = { onNext: () => void };

export function DoctorStep({ onNext }: Props) {
  const { saveDoctor } = useOnboardingMutations();
  const [photoFile, setPhotoFile] = useState<File | undefined>();
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const form = useForm<DoctorProfileValues>({
    resolver: zodResolver(doctorProfileSchema),
    defaultValues: {
      specialty_key: "",
      specialty_other: "",
      prc_license_number: "",
      consultation_fee: 0,
      follow_up_fee: 0,
    },
  });

  async function onSubmit(values: DoctorProfileValues) {
    const profile = await saveDoctor.mutateAsync({
      specialty_key: values.specialty_key,
      specialty_other:
        values.specialty_key === "other"
          ? values.specialty_other?.trim()
          : undefined,
      prc_license_number: values.prc_license_number,
      consultation_fee: values.consultation_fee,
      follow_up_fee: values.follow_up_fee,
    });
    if (photoFile) {
      setUploadingPhoto(true);
      try {
        const { upload_url } = await api.photoUpload(profile.id, {
          content_type: photoFile.type,
          file_size_bytes: photoFile.size,
        });
        await fetch(upload_url, {
          method: "PUT",
          body: photoFile,
          headers: { "Content-Type": photoFile.type },
        });
      } finally {
        setUploadingPhoto(false);
      }
    }
    onNext();
  }

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={form.handleSubmit(onSubmit)}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-4">
          <SpecialtySelect
            specialtyKey={form.watch("specialty_key")}
            specialtyOther={form.watch("specialty_other") ?? ""}
            onKeyChange={(key) => {
              form.setValue("specialty_key", key, { shouldValidate: true });
              if (key !== "other") form.setValue("specialty_other", "");
            }}
            onOtherChange={(value) =>
              form.setValue("specialty_other", value, { shouldValidate: true })
            }
            keyError={form.formState.errors.specialty_key?.message}
            otherError={form.formState.errors.specialty_other?.message}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="prc_license_number">PRC license</Label>
          <Input
            id="prc_license_number"
            {...form.register("prc_license_number")}
          />
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="consultation_fee">Consultation fee</Label>
        <Input
          id="consultation_fee"
          type="number"
          step="0.01"
          {...form.register("consultation_fee")}
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="photo">Photo</Label>
        <ImageFileDropzone
          id="photo"
          accept="image/png,image/jpeg,image/webp"
          imageUrl={photoPreview}
          uploading={uploadingPhoto}
          emptyLabel="Upload"
          onFileSelect={(file) => {
            if (photoPreview) URL.revokeObjectURL(photoPreview);
            setPhotoFile(file);
            setPhotoPreview(file ? URL.createObjectURL(file) : null);
          }}
          onRemove={() => {
            if (photoPreview) URL.revokeObjectURL(photoPreview);
            setPhotoFile(undefined);
            setPhotoPreview(null);
          }}
        />
      </div>
      <Button
        type="submit"
        className="mt-2 w-fit"
        disabled={saveDoctor.isPending || uploadingPhoto}
      >
        {saveDoctor.isPending || uploadingPhoto ? "Saving…" : "Continue"}
      </Button>
    </form>
  );
}
