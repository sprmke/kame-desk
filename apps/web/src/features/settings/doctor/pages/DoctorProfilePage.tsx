import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { doctorProfileSchema } from "@/features/onboarding/lib/schemas";
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

  useEffect(() => {
    return () => {
      if (signaturePreview) URL.revokeObjectURL(signaturePreview);
    };
  }, [signaturePreview]);

  const form = useForm({
    resolver: zodResolver(doctorProfileSchema),
    values: profile
      ? {
          specialty: profile.specialty ?? "",
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

  async function uploadSignature(file: File | undefined) {
    if (!file || !profile) return;
    if (signaturePreview) URL.revokeObjectURL(signaturePreview);
    const preview = URL.createObjectURL(file);
    setSignaturePreview(preview);
    setUploadingSignature(true);
    try {
      const { upload_url } = await api.signatureUpload(profile.id, {
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
      setSignaturePreview(null);
    } finally {
      setUploadingSignature(false);
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
        onSubmit={form.handleSubmit((v) => save.mutate(v))}
      >
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="specialty">Specialty</Label>
          <Input id="specialty" {...form.register("specialty")} />
        </div>
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
          <Label htmlFor="signature">Signature</Label>
          <ImageFileDropzone
            id="signature"
            accept="image/png,image/jpeg,image/webp"
            imageUrl={signaturePreview}
            uploading={uploadingSignature}
            disabled={!profile}
            emptyLabel="Upload"
            onFileSelect={(file) => void uploadSignature(file)}
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
