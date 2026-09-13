import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import {
  mergeNotificationPreferences,
  type ChronicRule,
} from "../lib/preferences";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  SettingsRow,
  SettingsSection,
} from "@/components/settings/SettingsSection";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { FORM_PLACEHOLDERS } from "@/lib/formPlaceholders";
import { NotificationsSettingsSkeleton } from "@/components/skeletons/PageSkeletons";

export function NotificationsSettingsPage() {
  const clinicId = getClinicId();
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["notification-preferences", clinicId],
    queryFn: () => api.getNotificationPreferences(clinicId!),
    enabled: Boolean(clinicId),
  });

  const prefs = mergeNotificationPreferences(data?.preferences);
  const [emailEnabled, setEmailEnabled] = useState(prefs.email_enabled);
  const [smsEnabled, setSmsEnabled] = useState(prefs.sms_enabled);
  const [whatsappEnabled, setWhatsappEnabled] = useState(
    prefs.whatsapp_enabled,
  );
  const [confirmation, setConfirmation] = useState(prefs.confirmation_enabled);
  const [reminder24h, setReminder24h] = useState(prefs.reminder_24h_enabled);
  const [reminder2h, setReminder2h] = useState(prefs.reminder_2h_enabled);
  const [senderName, setSenderName] = useState(prefs.sender_name ?? "");
  const [twilioSid, setTwilioSid] = useState("");
  const [twilioToken, setTwilioToken] = useState("");
  const [twilioFrom, setTwilioFrom] = useState("");
  const [whatsappPhoneId, setWhatsappPhoneId] = useState("");
  const [whatsappToken, setWhatsappToken] = useState("");
  const [rules, setRules] = useState<ChronicRule[]>([]);
  const [ruleCondition, setRuleCondition] = useState("");
  const [ruleMonths, setRuleMonths] = useState("3");

  useEffect(() => {
    setRules(prefs.chronic_condition_rules);
  }, [data]);

  const save = useMutation({
    mutationFn: () =>
      api.patchNotificationPreferences(clinicId!, {
        email_enabled: emailEnabled,
        sms_enabled: smsEnabled,
        whatsapp_enabled: whatsappEnabled,
        confirmation_enabled: confirmation,
        reminder_24h_enabled: reminder24h,
        reminder_2h_enabled: reminder2h,
        sender_name: senderName || null,
        chronic_condition_rules: rules,
        ...(smsEnabled && !data?.sms_configured
          ? {
              twilio_account_sid: twilioSid,
              twilio_auth_token: twilioToken,
              twilio_from_number: twilioFrom,
            }
          : {}),
        ...(whatsappEnabled && !data?.whatsapp_configured
          ? {
              whatsapp_phone_number_id: whatsappPhoneId,
              whatsapp_access_token: whatsappToken,
            }
          : {}),
      }),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: ["notification-preferences", clinicId],
      });
    },
  });

  if (isLoading) {
    return (
      <div className="w-full">
        <PageHeader title="Notifications" />
        <NotificationsSettingsSkeleton />
      </div>
    );
  }

  return (
    <div className="w-full">
      <PageHeader title="Notifications" />

      <form
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate();
        }}
      >
        <SettingsSection title="Channels">
          <SettingsRow label="Email">
            <Switch
              id="email-enabled"
              checked={emailEnabled}
              onCheckedChange={setEmailEnabled}
            />
          </SettingsRow>
          <SettingsRow label="SMS">
            <Switch
              id="sms-enabled"
              checked={smsEnabled}
              onCheckedChange={setSmsEnabled}
            />
          </SettingsRow>
          <SettingsRow label="WhatsApp">
            <Switch
              id="whatsapp-enabled"
              checked={whatsappEnabled}
              onCheckedChange={setWhatsappEnabled}
            />
          </SettingsRow>
        </SettingsSection>

        <SettingsSection title="Reminders">
          <SettingsRow label="Booking confirmation">
            <Switch
              id="confirmation"
              checked={confirmation}
              onCheckedChange={setConfirmation}
            />
          </SettingsRow>
          <SettingsRow label="24 hour reminder">
            <Switch
              id="reminder-24h"
              checked={reminder24h}
              onCheckedChange={setReminder24h}
            />
          </SettingsRow>
          <SettingsRow label="2 hour reminder">
            <Switch
              id="reminder-2h"
              checked={reminder2h}
              onCheckedChange={setReminder2h}
            />
          </SettingsRow>
          <SettingsRow label="Sender name">
            <Input
              id="sender-name"
              value={senderName}
              onChange={(e) => setSenderName(e.target.value)}
              placeholder={FORM_PLACEHOLDERS.clinicName}
            />
          </SettingsRow>
        </SettingsSection>

        <SettingsSection title="Recall rules">
          <div className="grid gap-3 py-3 sm:grid-cols-[2fr_1fr_auto] sm:items-end">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="rule-condition">Condition</Label>
              <Input
                id="rule-condition"
                value={ruleCondition}
                onChange={(e) => setRuleCondition(e.target.value)}
                placeholder={FORM_PLACEHOLDERS.condition}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="rule-months">Months</Label>
              <Input
                id="rule-months"
                type="number"
                min={1}
                max={36}
                value={ruleMonths}
                onChange={(e) => setRuleMonths(e.target.value)}
              />
            </div>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                if (!ruleCondition.trim()) return;
                setRules([
                  ...rules,
                  {
                    condition: ruleCondition.trim(),
                    interval_months: Number(ruleMonths) || 3,
                  },
                ]);
                setRuleCondition("");
              }}
            >
              Add
            </Button>
          </div>
          {rules.map((rule, index) => (
            <div
              key={`${rule.condition}-${index}`}
              className="flex items-center justify-between text-sm"
            >
              <span>
                {rule.condition} · every {rule.interval_months} months
              </span>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setRules(rules.filter((_, i) => i !== index))}
              >
                Remove
              </Button>
            </div>
          ))}
        </SettingsSection>

        {smsEnabled && (
          <SettingsSection title="SMS provider (Twilio)">
            {data?.sms_configured ? (
              <p className="text-sm text-muted-foreground">
                SMS credentials saved
              </p>
            ) : (
              <>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="twilio-sid">Account SID</Label>
                  <Input
                    id="twilio-sid"
                    value={twilioSid}
                    onChange={(e) => setTwilioSid(e.target.value)}
                    required
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="twilio-token">Auth token</Label>
                  <Input
                    id="twilio-token"
                    type="password"
                    value={twilioToken}
                    onChange={(e) => setTwilioToken(e.target.value)}
                    required
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="twilio-from">From number</Label>
                  <Input
                    id="twilio-from"
                    value={twilioFrom}
                    onChange={(e) => setTwilioFrom(e.target.value)}
                    required
                  />
                </div>
              </>
            )}
          </SettingsSection>
        )}

        {whatsappEnabled && (
          <SettingsSection title="WhatsApp provider (Meta Business Cloud API)">
            {data?.whatsapp_configured ? (
              <p className="text-sm text-muted-foreground">
                WhatsApp credentials saved
              </p>
            ) : (
              <>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="whatsapp-phone-id">Phone number ID</Label>
                  <Input
                    id="whatsapp-phone-id"
                    value={whatsappPhoneId}
                    onChange={(e) => setWhatsappPhoneId(e.target.value)}
                    required
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="whatsapp-token">Access token</Label>
                  <Input
                    id="whatsapp-token"
                    type="password"
                    value={whatsappToken}
                    onChange={(e) => setWhatsappToken(e.target.value)}
                    required
                  />
                </div>
              </>
            )}
          </SettingsSection>
        )}

        <div className="flex items-center gap-3">
          <Button type="submit" disabled={save.isPending}>
            {save.isPending ? "Saving…" : "Save"}
          </Button>
          {save.isError && (
            <p className="text-sm text-destructive">Could not save settings</p>
          )}
        </div>
      </form>
    </div>
  );
}
