import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { SpecialtySelect } from "@/features/onboarding/components/SpecialtySelect";
import {
  doctorProfileSchema,
  type DoctorProfileValues,
} from "@/features/onboarding/lib/schemas";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { specialtyKeyFromLegacyLabel } from "@/lib/doctorSpecialties";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { ImageFileDropzone } from "@/components/ui/file-dropzone";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DoctorProfileSkeleton } from "@/components/skeletons/PageSkeletons";

export function DoctorProfilePage() {
  const clinicId = getClinicId()!;
  const qc = useQueryClient();
  const { data: me } = useQuery({ queryKey: ["me"], queryFn: () => api.me() });
  const { data: doctors } = useQuery({
    queryKey: ["doctors", clinicId],
    queryFn: () => api.listDoctors(clinicId),
  });

  const profile =
    doctors?.find((d) => d.user_id === me?.id) ?? doctors?.[0] ?? null;
  const [signaturePreview, setSignaturePreview] = useState<string | null>(null);
  const [uploadingSignature, setUploadingSignature] = useState(false);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);

  useEffect(() => {
    return () => {
      if (signaturePreview) URL.revokeObjectURL(signaturePreview);
      if (photoPreview) URL.revokeObjectURL(photoPreview);
    };
  }, [signaturePreview, photoPreview]);

  const form = useForm<DoctorProfileValues>({
    resolver: zodResolver(doctorProfileSchema),
    values: profile
      ? {
          specialty_key:
            profile.specialty_key ??
            specialtyKeyFromLegacyLabel(profile.specialty),
          specialty_other:
            profile.specialty_other ??
            ((profile.specialty_key ??
              specialtyKeyFromLegacyLabel(profile.specialty)) === "other"
              ? (profile.specialty ?? "")
              : ""),
          prc_license_number: profile.prc_license_number ?? "",
          consultation_fee: Number(profile.consultation_fee ?? 0),
          follow_up_fee: profile.follow_up_fee
            ? Number(profile.follow_up_fee)
            : undefined,
        }
      : undefined,
  });

  const save = useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      profile
        ? api.patchDoctor(profile.id, body)
        : api.createDoctor(clinicId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["doctors", clinicId] }),
  });

  async function uploadImage(
    file: File | undefined,
    kind: "signature" | "photo",
  ) {
    if (!file || !profile) return;
    const setPreview =
      kind === "signature" ? setSignaturePreview : setPhotoPreview;
    const setUploading =
      kind === "signature" ? setUploadingSignature : setUploadingPhoto;
    const current = kind === "signature" ? signaturePreview : photoPreview;
    if (current) URL.revokeObjectURL(current);
    const preview = URL.createObjectURL(file);
    setPreview(preview);
    setUploading(true);
    try {
      const request =
        kind === "signature" ? api.signatureUpload : api.photoUpload;
      const { upload_url } = await request(profile.id, {
        content_type: file.type,
        file_size_bytes: file.size,
      });
      await fetch(upload_url, {
        method: "PUT",
        body: file,
        headers: { "Content-Type": file.type },
      });
      qc.invalidateQueries({ queryKey: ["doctors", clinicId] });
    } catch {
      URL.revokeObjectURL(preview);
      setPreview(null);
    } finally {
      setUploading(false);
    }
  }

  if (!profile && !doctors) {
    return (
      <div className="w-full">
        <PageHeader title="Doctor profile" />
        <DoctorProfileSkeleton />
      </div>
    );
  }

  return (
    <div className="w-full">
      <PageHeader title="Doctor profile" />
      <form
        className="flex flex-col gap-4"
        onSubmit={form.handleSubmit((values) =>
          save.mutate({
            specialty_key: values.specialty_key,
            specialty_other:
              values.specialty_key === "other"
                ? values.specialty_other?.trim()
                : null,
            prc_license_number: values.prc_license_number,
            consultation_fee: values.consultation_fee,
            follow_up_fee: values.follow_up_fee,
          }),
        )}
      >
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
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="prc-license">PRC license</Label>
          <Input id="prc-license" {...form.register("prc_license_number")} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="consultation-fee">Consultation fee</Label>
            <Input
              id="consultation-fee"
              type="number"
              step="0.01"
              {...form.register("consultation_fee")}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="follow-up-fee">Follow-up fee</Label>
            <Input
              id="follow-up-fee"
              type="number"
              step="0.01"
              {...form.register("follow_up_fee")}
            />
          </div>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="photo">Photo</Label>
          <ImageFileDropzone
            id="photo"
            accept="image/png,image/jpeg,image/webp"
            imageUrl={photoPreview}
            uploading={uploadingPhoto}
            disabled={!profile}
            emptyLabel="Upload"
            onFileSelect={(file) => void uploadImage(file, "photo")}
            onRemove={() => {
              if (photoPreview) URL.revokeObjectURL(photoPreview);
              setPhotoPreview(null);
            }}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="signature">Signature</Label>
          <ImageFileDropzone
            id="signature"
            accept="image/png,image/jpeg,image/webp"
            imageUrl={signaturePreview}
            uploading={uploadingSignature}
            disabled={!profile}
            emptyLabel="Upload"
            onFileSelect={(file) => void uploadImage(file, "signature")}
            onRemove={() => {
              if (signaturePreview) URL.revokeObjectURL(signaturePreview);
              setSignaturePreview(null);
            }}
          />
        </div>
        <Button type="submit" disabled={save.isPending} className="w-fit">
          {save.isPending ? "Saving…" : "Save"}
        </Button>
      </form>
    </div>
  );
}
