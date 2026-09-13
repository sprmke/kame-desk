export type ChronicRule = {
  condition: string;
  interval_months: number;
};

export type NotificationPreferences = {
  email_enabled: boolean;
  sms_enabled: boolean;
  whatsapp_enabled: boolean;
  confirmation_enabled: boolean;
  reminder_24h_enabled: boolean;
  reminder_2h_enabled: boolean;
  sender_name: string | null;
  chronic_condition_rules: ChronicRule[];
};

export const DEFAULT_NOTIFICATION_PREFERENCES: NotificationPreferences = {
  email_enabled: true,
  sms_enabled: false,
  whatsapp_enabled: false,
  confirmation_enabled: true,
  reminder_24h_enabled: true,
  reminder_2h_enabled: false,
  sender_name: null,
  chronic_condition_rules: [],
};

export function mergeNotificationPreferences(
  prefs: Partial<NotificationPreferences> | null | undefined,
): NotificationPreferences {
  return {
    ...DEFAULT_NOTIFICATION_PREFERENCES,
    ...(prefs ?? {}),
    chronic_condition_rules: prefs?.chronic_condition_rules ?? [],
  };
}

export const RECALL_STATUSES = [
  "pending",
  "contacted",
  "booked",
  "dismissed",
] as const;

export type RecallStatus = (typeof RECALL_STATUSES)[number];

export function isRecallStatus(value: string): value is RecallStatus {
  return (RECALL_STATUSES as readonly string[]).includes(value);
}
