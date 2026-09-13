import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";

export function useOnboardingStatus() {
  const clinicId = getClinicId();
  return useQuery({
    queryKey: ["onboarding-status", clinicId],
    queryFn: () => api.getOnboardingStatus(clinicId!),
    enabled: Boolean(clinicId),
  });
}

export function useOnboardingMutations() {
  const clinicId = getClinicId()!;
  const qc = useQueryClient();
  const invalidate = () =>
    qc.invalidateQueries({ queryKey: ["onboarding-status", clinicId] });

  return {
    saveClinic: useMutation({
      mutationFn: (body: Record<string, unknown>) =>
        api.patchClinic(clinicId, body),
      onSuccess: invalidate,
    }),
    saveDoctor: useMutation({
      mutationFn: (body: Record<string, unknown>) =>
        api.createDoctor(clinicId, body),
      onSuccess: invalidate,
    }),
    saveHours: useMutation({
      mutationFn: (body: {
        working_hours: Record<
          string,
          { open: string; close: string; closed: boolean }
        >;
        holiday_dates: string[];
      }) => api.putWorkingHours(clinicId, body),
      onSuccess: invalidate,
    }),
    saveFee: useMutation({
      mutationFn: (body: { name: string; amount: number }) =>
        api.createServiceFee(clinicId, body),
      onSuccess: invalidate,
    }),
    invite: useMutation({
      mutationFn: (body: { email: string; role: string }) =>
        api.createInvitation(clinicId, body),
      onSuccess: invalidate,
    }),
    skipInvite: useMutation({
      mutationFn: () => api.skipInvite(clinicId),
      onSuccess: invalidate,
    }),
  };
}
