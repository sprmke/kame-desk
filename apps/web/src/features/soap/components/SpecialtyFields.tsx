import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Odontogram } from "@/features/soap/components/Odontogram";

type SpecialtyFieldsProps = {
  templateKey: string;
  value: Record<string, unknown>;
  onChange: (next: Record<string, unknown>) => void;
  disabled?: boolean;
  patientId?: string;
  appointmentId?: string;
  soapNoteId?: string;
};

function setField(
  value: Record<string, unknown>,
  onChange: SpecialtyFieldsProps["onChange"],
  patch: Record<string, unknown>,
) {
  onChange({ ...value, ...patch, schema_version: 1 });
}

export function SpecialtyFields({
  templateKey,
  value,
  onChange,
  disabled,
  patientId,
  appointmentId,
  soapNoteId,
}: SpecialtyFieldsProps) {
  if (templateKey === "dental") {
    if (!patientId) return null;
    return (
      <div className="flex flex-col gap-2">
        <Odontogram
          patientId={patientId}
          appointmentId={appointmentId}
          soapNoteId={soapNoteId}
          disabled={disabled}
        />
        <Label htmlFor="dental-notes">Notes</Label>
        <Textarea
          id="dental-notes"
          rows={2}
          value={(value.teeth as string) ?? ""}
          disabled={disabled}
          placeholder="Additional dental notes"
          onChange={(e) => setField(value, onChange, { teeth: e.target.value })}
        />
      </div>
    );
  }

  if (templateKey === "pediatric") {
    return (
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="height_cm">Height (cm)</Label>
          <Input
            id="height_cm"
            value={(value.height_cm as string) ?? ""}
            disabled={disabled}
            onChange={(e) =>
              setField(value, onChange, { height_cm: e.target.value })
            }
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="weight_kg">Weight (kg)</Label>
          <Input
            id="weight_kg"
            value={(value.weight_kg as string) ?? ""}
            disabled={disabled}
            onChange={(e) =>
              setField(value, onChange, { weight_kg: e.target.value })
            }
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="growth_percentile">Percentile</Label>
          <Input
            id="growth_percentile"
            value={(value.growth_percentile as string) ?? ""}
            disabled={disabled}
            onChange={(e) =>
              setField(value, onChange, { growth_percentile: e.target.value })
            }
          />
        </div>
      </div>
    );
  }

  if (templateKey === "obgyn") {
    return (
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="gravida">Gravida</Label>
          <Input
            id="gravida"
            value={(value.gravida as string) ?? ""}
            disabled={disabled}
            onChange={(e) =>
              setField(value, onChange, { gravida: e.target.value })
            }
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="para">Para</Label>
          <Input
            id="para"
            value={(value.para as string) ?? ""}
            disabled={disabled}
            onChange={(e) =>
              setField(value, onChange, { para: e.target.value })
            }
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="lmp">LMP</Label>
          <Input
            id="lmp"
            value={(value.lmp as string) ?? ""}
            disabled={disabled}
            onChange={(e) => setField(value, onChange, { lmp: e.target.value })}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="edd">EDD</Label>
          <Input
            id="edd"
            value={(value.edd as string) ?? ""}
            disabled={disabled}
            onChange={(e) => setField(value, onChange, { edd: e.target.value })}
          />
        </div>
      </div>
    );
  }

  if (templateKey === "psychiatry") {
    return (
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="mse">Mental status</Label>
          <Textarea
            id="mse"
            rows={2}
            value={(value.mental_status as string) ?? ""}
            disabled={disabled}
            onChange={(e) =>
              setField(value, onChange, { mental_status: e.target.value })
            }
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="risk">Risk</Label>
          <Input
            id="risk"
            value={(value.risk as string) ?? ""}
            disabled={disabled}
            onChange={(e) =>
              setField(value, onChange, { risk: e.target.value })
            }
          />
        </div>
      </div>
    );
  }

  if (templateKey === "dermatology") {
    return (
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="lesion_location">Location</Label>
          <Input
            id="lesion_location"
            value={(value.lesion_location as string) ?? ""}
            disabled={disabled}
            onChange={(e) =>
              setField(value, onChange, { lesion_location: e.target.value })
            }
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="morphology">Morphology</Label>
          <Input
            id="morphology"
            value={(value.morphology as string) ?? ""}
            disabled={disabled}
            onChange={(e) =>
              setField(value, onChange, { morphology: e.target.value })
            }
          />
        </div>
      </div>
    );
  }

  return null;
}
