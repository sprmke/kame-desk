import type { LucideIcon } from "lucide-react";
import {
  AlertTriangle,
  Bell,
  CalendarDays,
  CreditCard,
  FileText,
  MessageSquare,
  Pill,
  Shield,
  UserPlus,
  Users,
} from "lucide-react";

export type NotificationType =
  | "appointment.public_booked"
  | "appointment.needs_confirm"
  | "appointment.patient_reschedule_requested"
  | "appointment.cancelled"
  | "appointment.no_show"
  | "appointment.rescheduled"
  | "visit.arrived"
  | "visit.completed"
  | "waitlist.created"
  | "waitlist.slot_offered"
  | "prescription.issued"
  | "document.issued"
  | "transcription.ready"
  | "visit_summary.failed"
  | "clinical_order.updated"
  | "invoice.payment_recorded"
  | "invoice.voided"
  | "invoice.credit_issued"
  | "insurance_claim.denied"
  | "loa_request.status_changed"
  | "eligibility_check.updated"
  | "reminder.send_failed"
  | "messaging.inbound"
  | "staff.joined"
  | "membership.role_changed"
  | "auth.refresh_reuse"
  | "clinic.deletion_requested";

const NOTIFICATION_ICONS: Record<NotificationType, LucideIcon> = {
  "appointment.public_booked": CalendarDays,
  "appointment.needs_confirm": CalendarDays,
  "appointment.patient_reschedule_requested": CalendarDays,
  "appointment.cancelled": CalendarDays,
  "appointment.no_show": CalendarDays,
  "appointment.rescheduled": CalendarDays,
  "visit.arrived": Users,
  "visit.completed": Users,
  "waitlist.created": CalendarDays,
  "waitlist.slot_offered": CalendarDays,
  "prescription.issued": Pill,
  "document.issued": FileText,
  "transcription.ready": FileText,
  "visit_summary.failed": AlertTriangle,
  "clinical_order.updated": FileText,
  "invoice.payment_recorded": CreditCard,
  "invoice.voided": CreditCard,
  "invoice.credit_issued": CreditCard,
  "insurance_claim.denied": Shield,
  "loa_request.status_changed": Shield,
  "eligibility_check.updated": Shield,
  "reminder.send_failed": AlertTriangle,
  "messaging.inbound": MessageSquare,
  "staff.joined": UserPlus,
  "membership.role_changed": UserPlus,
  "auth.refresh_reuse": AlertTriangle,
  "clinic.deletion_requested": AlertTriangle,
};

export function notificationIconFor(type: string): LucideIcon {
  return NOTIFICATION_ICONS[type as NotificationType] ?? Bell;
}

export function formatRelativeTime(iso: string): string {
  const date = new Date(iso);
  const diff = Date.now() - date.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Now";
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  return `${days}d`;
}
