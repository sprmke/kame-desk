import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { Button } from "@/components/ui/button";
import { SearchInput } from "@/components/ui/search-input";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ResponsiveModal,
  ResponsiveModalContent,
  ResponsiveModalFooter,
  ResponsiveModalHeader,
  ResponsiveModalTitle,
} from "@/components/ui/responsive-modal";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDone: () => void;
};

export function WalkInDialog({ open, onOpenChange, onDone }: Props) {
  const clinicId = getClinicId();
  const [query, setQuery] = useState("");
  const [name, setName] = useState("");
  const [reason, setReason] = useState("");
  const [patientId, setPatientId] = useState<string | null>(null);

  const { data: doctors } = useQuery({
    queryKey: ["doctors-walkin", clinicId],
    queryFn: () => api.listDoctors(clinicId!),
    enabled: Boolean(clinicId) && open,
  });
  const { data: searchResults } = useQuery({
    queryKey: ["walkin-patient-search", query],
    queryFn: () => api.listPatients({ q: query, page_size: 8 }),
    enabled: open && query.trim().length > 1,
  });
  const [selectedDoctor, setSelectedDoctor] = useState("");
  useEffect(() => {
    if (doctors?.length && !selectedDoctor) {
      setSelectedDoctor(doctors[0].id);
    }
  }, [doctors, selectedDoctor]);

  const matches = useMemo(() => searchResults?.items ?? [], [searchResults]);

  const walkIn = useMutation({
    mutationFn: () => {
      if (patientId) {
        return api.createWalkIn({
          doctor_id: selectedDoctor,
          patient_id: patientId,
          reason_for_visit: reason || undefined,
        });
      }
      return api.createWalkIn({
        doctor_id: selectedDoctor,
        new_patient: { full_name: name },
        reason_for_visit: reason || undefined,
      });
    },
    onSuccess: () => {
      setName("");
      setReason("");
      setQuery("");
      setPatientId(null);
      onDone();
    },
  });

  const canSubmit = Boolean(selectedDoctor && (patientId || name.trim()));

  return (
    <ResponsiveModal open={open} onOpenChange={onOpenChange}>
      <ResponsiveModalContent className="max-w-sm" data-testid="walk-in-modal">
        <ResponsiveModalHeader>
          <ResponsiveModalTitle>Walk-in</ResponsiveModalTitle>
        </ResponsiveModalHeader>
        <form
          className="flex flex-col gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            if (!canSubmit) return;
            walkIn.mutate();
          }}
        >
          <div className="relative">
            <SearchInput
              placeholder={FORM_PLACEHOLDERS.searchPatients}
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPatientId(null);
              }}
            />
            {matches.length > 0 && !patientId && (
              <ul className="absolute z-10 mt-1 max-h-40 w-full overflow-y-auto rounded-lg border border-border bg-popover text-sm shadow-theme-md">
                {matches.map((p) => (
                  <li key={p.id}>
                    <button
                      type="button"
                      className="min-h-[44px] w-full px-3 py-2 text-left hover:bg-secondary"
                      onClick={() => {
                        setPatientId(p.id);
                        setName(p.full_name);
                        setQuery(p.full_name);
                      }}
                    >
                      {p.full_name}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          {!patientId && (
            <Input
              placeholder={FORM_PLACEHOLDERS.fullName}
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          )}
          {doctors && doctors.length > 1 && (
            <Select value={selectedDoctor} onValueChange={setSelectedDoctor}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {doctors.map((d) => (
                  <SelectItem key={d.id} value={d.id}>
                    {d.full_name?.trim() || "Doctor"}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <Input
            placeholder={FORM_PLACEHOLDERS.reasonForVisit}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
          <ResponsiveModalFooter>
            <Button
              type="submit"
              disabled={walkIn.isPending || !canSubmit}
              className="w-full sm:w-fit"
            >
              {walkIn.isPending ? "Adding…" : "Add walk-in"}
            </Button>
          </ResponsiveModalFooter>
        </form>
      </ResponsiveModalContent>
    </ResponsiveModal>
  );
}
