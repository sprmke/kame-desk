import { Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ChevronLeft } from "lucide-react";
import { api } from "@/lib/apiClient";
import {
  patientFormSchema,
  type PatientFormValues,
} from "@/features/patients/lib/schemas";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { pageContainerClass } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DatePicker } from "@/components/ui/date-picker";
import { todayIsoManila } from "@/lib/isoDate";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Field, FieldError } from "@/components/forms/Field";
import { FieldLabel } from "@/components/forms/FieldLabel";

export function PatientNewPage() {
  const navigate = useNavigate();
  const form = useForm<PatientFormValues>({
    resolver: zodResolver(patientFormSchema),
    defaultValues: { full_name: "", data_processing_consent: false },
  });
  const watchedName = form.watch("full_name");
  const watchedContact = form.watch("contact_number");

  const { data: matches } = useQuery({
    queryKey: ["patient-matches", watchedName, watchedContact],
    queryFn: () =>
      api.findPatientMatches({
        full_name: watchedName || undefined,
        contact_number: watchedContact || undefined,
      }),
    enabled: Boolean((watchedName && watchedName.length > 2) || watchedContact),
  });

  const create = useMutation({
    mutationFn: (values: PatientFormValues) =>
      api.createPatient({
        ...values,
        email: values.email || undefined,
        birthdate: values.birthdate || undefined,
        insurance_info:
          values.insurance_provider || values.insurance_member_id
            ? {
                provider: values.insurance_provider || null,
                member_id: values.insurance_member_id || null,
              }
            : undefined,
      }),
    onSuccess: (patient) => {
      navigate({
        to: "/dashboard/patients/$patientId",
        params: { patientId: patient.id },
      });
    },
  });

  return (
    <div className={pageContainerClass("narrow")}>
      <Link
        to="/dashboard/patients"
        className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ChevronLeft className="size-4" />
        Patients
      </Link>
      <PageHeader title="New patient" />

      {(matches ?? []).length > 0 && (
        <Card className="mb-4">
          <CardContent className="pt-5 text-sm">
            <p className="mb-2 font-medium">Possible matches</p>
            <ul className="flex flex-col gap-1">
              {matches?.map((m) => (
                <li key={m.id}>
                  <Link
                    to="/dashboard/patients/$patientId"
                    params={{ patientId: m.id }}
                    className="text-primary hover:underline"
                  >
                    {m.full_name}
                  </Link>
                  {m.contact_number ? ` · ${m.contact_number}` : ""}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="pt-5">
          <form
            className="flex flex-col gap-4"
            onSubmit={form.handleSubmit((v) => create.mutate(v))}
          >
            <Field>
              <FieldLabel htmlFor="full_name" label="Full name" required />
              <Input
                id="full_name"
                placeholder={FORM_PLACEHOLDERS.fullName}
                {...form.register("full_name")}
              />
              <FieldError>
                {form.formState.errors.full_name?.message}
              </FieldError>
            </Field>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field>
                <FieldLabel htmlFor="birthdate" label="Birthdate" />
                <DatePicker
                  id="birthdate"
                  {...form.register("birthdate")}
                  value={form.watch("birthdate") ?? ""}
                  max={todayIsoManila()}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="contact_number" label="Contact" />
                <Input
                  id="contact_number"
                  placeholder={FORM_PLACEHOLDERS.phone}
                  {...form.register("contact_number")}
                />
              </Field>
            </div>

            <Field>
              <FieldLabel htmlFor="email" label="Email" />
              <Input
                id="email"
                type="email"
                placeholder={FORM_PLACEHOLDERS.email}
                {...form.register("email")}
              />
            </Field>

            <Field>
              <FieldLabel htmlFor="address" label="Address" />
              <Textarea
                id="address"
                rows={2}
                placeholder={FORM_PLACEHOLDERS.address}
                {...form.register("address")}
              />
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field>
                <FieldLabel htmlFor="hmo" label="HMO" />
                <Input
                  id="hmo"
                  placeholder={FORM_PLACEHOLDERS.hmo}
                  {...form.register("insurance_provider")}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="member-id" label="Member ID" />
                <Input
                  id="member-id"
                  placeholder={FORM_PLACEHOLDERS.memberId}
                  {...form.register("insurance_member_id")}
                />
              </Field>
            </div>

            <label className="flex items-start gap-2.5 text-sm">
              <Checkbox
                className="mt-0.5"
                onCheckedChange={(checked) =>
                  form.setValue("data_processing_consent", checked === true)
                }
              />
              <span className="text-foreground">
                Patient consents to clinic data processing
              </span>
            </label>
            <FieldError>
              {form.formState.errors.data_processing_consent?.message}
            </FieldError>

            {create.isError && (
              <p className="text-sm text-destructive">{create.error.message}</p>
            )}

            <Button type="submit" className="w-fit" disabled={create.isPending}>
              {create.isPending ? "Saving…" : "Save"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
