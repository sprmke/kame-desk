import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DOCTOR_SPECIALTIES } from "@/lib/doctorSpecialties";

type Props = {
  specialtyKey: string;
  specialtyOther: string;
  onKeyChange: (key: string) => void;
  onOtherChange: (value: string) => void;
  keyError?: string;
  otherError?: string;
};

export function SpecialtySelect({
  specialtyKey,
  specialtyOther,
  onKeyChange,
  onOtherChange,
  keyError,
  otherError,
}: Props) {
  return (
    <>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="specialty_key">Specialty</Label>
        <Select value={specialtyKey || undefined} onValueChange={onKeyChange}>
          <SelectTrigger id="specialty_key" className="w-full">
            <SelectValue placeholder="Select" />
          </SelectTrigger>
          <SelectContent>
            {DOCTOR_SPECIALTIES.map((item) => (
              <SelectItem key={item.key} value={item.key}>
                {item.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {keyError ? (
          <p className="text-sm text-destructive">{keyError}</p>
        ) : null}
      </div>
      {specialtyKey === "other" ? (
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="specialty_other">Specialty name</Label>
          <Input
            id="specialty_other"
            value={specialtyOther}
            onChange={(event) => onOtherChange(event.target.value)}
          />
          {otherError ? (
            <p className="text-sm text-destructive">{otherError}</p>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
