import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, type Appointment } from "@/lib/apiClient";
import { Button } from "@/components/ui/button";
import {
  SeriesScopeDialog,
  type SeriesScope,
} from "@/features/appointments/components/SeriesScopeDialog";

type Props = {
  appointment: Appointment;
};

function isPastEnd(iso: string) {
  return new Date(iso).getTime() < Date.now();
}

function isTerminal(status: string) {
  return ["Cancelled", "No Show", "Rescheduled"].includes(status);
}

export function useAppointmentRowActions(appointment: Appointment) {
  const queryClient = useQueryClient();
  const [scopeOpen, setScopeOpen] = useState(false);
  const cancel = useMutation({
    mutationFn: (scope: SeriesScope) =>
      api.cancelAppointment(appointment.id, scope),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      setScopeOpen(false);
    },
  });
  const noShow = useMutation({
    mutationFn: () => api.markNoShow(appointment.id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["appointments"] }),
  });

  const terminal = isTerminal(appointment.appointment_status);
  const canCancel = !terminal;
  const canNoShow = !terminal && isPastEnd(appointment.scheduled_end);

  return {
    canCancel,
    canNoShow,
    scopeOpen,
    setScopeOpen,
    onCancel: () => {
      if (appointment.series_id) setScopeOpen(true);
      else cancel.mutate("this");
    },
    onNoShow: () => noShow.mutate(),
    noShowPending: noShow.isPending,
    chooseScope: (scope: SeriesScope) => cancel.mutate(scope),
    hasSeries: Boolean(appointment.series_id),
  };
}

export function AppointmentRowActions({ appointment }: Props) {
  const actions = useAppointmentRowActions(appointment);

  if (!actions.canCancel && !actions.canNoShow) return null;

  return (
    <div
      className="mt-2 flex flex-wrap gap-2"
      onClick={(e) => e.stopPropagation()}
    >
      {actions.canCancel ? (
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={actions.onCancel}
        >
          Cancel
        </Button>
      ) : null}
      {actions.canNoShow ? (
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={actions.onNoShow}
          disabled={actions.noShowPending}
        >
          No show
        </Button>
      ) : null}
      <SeriesScopeDialog
        open={actions.scopeOpen}
        action="cancel"
        hasSeries={actions.hasSeries}
        onChoose={actions.chooseScope}
        onClose={() => actions.setScopeOpen(false)}
      />
    </div>
  );
}
