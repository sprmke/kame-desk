import { useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Search, User } from "lucide-react";
import { api } from "@/lib/apiClient";
import { useSession } from "@/hooks/useSession";
import type { Permission } from "@/lib/rbac";
import { listItemDelay } from "@/lib/motion";
import {
  ResponsiveModal,
  ResponsiveModalContent,
  ResponsiveModalTitle,
} from "@/components/ui/responsive-modal";

type Props = {
  open: boolean;
  onClose: () => void;
};

type CommandItem = {
  id: string;
  label: string;
  keywords: string;
  permission?: Permission;
  run: () => void;
};

export function CommandPalette({ open, onClose }: Props) {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const { can } = useSession();

  const staticCommands = useMemo<CommandItem[]>(
    () => [
      {
        id: "today",
        label: "Today",
        keywords: "dashboard home overview",
        permission: "today:view",
        run: () => navigate({ to: "/dashboard" }),
      },
      {
        id: "schedule",
        label: "Schedule",
        keywords: "appointments calendar",
        permission: "schedule:view",
        run: () => navigate({ to: "/dashboard/appointments" }),
      },
      {
        id: "waiting",
        label: "Waiting room",
        keywords: "waiting room queue",
        permission: "waiting_room:view",
        run: () => navigate({ to: "/dashboard/waiting-room" }),
      },
      {
        id: "patients",
        label: "Patients",
        keywords: "patients chart directory",
        permission: "patients:view",
        run: () => navigate({ to: "/dashboard/patients" }),
      },
      {
        id: "billing",
        label: "Billing",
        keywords: "billing invoices claims",
        permission: "billing:view",
        run: () => navigate({ to: "/dashboard/billing/invoices" }),
      },
      {
        id: "outreach",
        label: "Outreach",
        keywords: "reminders recalls",
        permission: "outreach:view",
        run: () => navigate({ to: "/dashboard/outreach/reminders" }),
      },
      {
        id: "documents",
        label: "Documents",
        keywords: "documents generate templates",
        permission: "documents:view",
        run: () => navigate({ to: "/dashboard/documents/generate" }),
      },
      {
        id: "insights",
        label: "Insights",
        keywords: "reports activity audit",
        permission: "insights:view",
        run: () => navigate({ to: "/dashboard/insights/reports" }),
      },
      {
        id: "settings",
        label: "Settings",
        keywords: "settings account team clinic",
        permission: "settings:account",
        run: () => navigate({ to: "/dashboard/settings/account" }),
      },
      {
        id: "open-assistant",
        label: "Open clinic assistant",
        keywords: "assistant chat ai help",
        run: () =>
          window.dispatchEvent(new CustomEvent("doctordesk:open-assistant")),
      },
      {
        id: "assistant-settings",
        label: "Assistant settings",
        keywords: "assistant settings ai",
        permission: "settings:assistant",
        run: () => navigate({ to: "/dashboard/settings/assistant" }),
      },
      {
        id: "new-appt",
        label: "New appointment",
        keywords: "book appointment new",
        permission: "schedule:write",
        run: () =>
          navigate({
            to: "/dashboard/appointments/new",
            search: { patientId: undefined },
          }),
      },
    ],
    [navigate],
  );

  const { data, isFetching } = useQuery({
    queryKey: ["command-palette-patients", q],
    queryFn: () => api.listPatients({ q, page_size: 8 }),
    enabled: open && q.trim().length > 1 && can("patients:view"),
  });

  const filteredStatic = staticCommands.filter((cmd) => {
    if (cmd.permission && !can(cmd.permission)) return false;
    const needle = q.trim().toLowerCase();
    if (!needle) return true;
    return (
      cmd.label.toLowerCase().includes(needle) ||
      cmd.keywords.toLowerCase().includes(needle)
    );
  });

  const reducedMotion = useReducedMotion();

  useEffect(() => {
    if (!open) setQ("");
  }, [open]);

  return (
    <ResponsiveModal open={open} onOpenChange={(next) => !next && onClose()}>
      <ResponsiveModalContent
        className="max-w-md gap-0 p-0 sm:p-0"
        showCloseButton={false}
        aria-label="Command palette"
      >
        <ResponsiveModalTitle className="sr-only">
          Command palette
        </ResponsiveModalTitle>
        <div className="flex items-center gap-2 border-b border-border px-4">
          <Search className="size-4 shrink-0 text-muted-foreground" />
          <input
            autoFocus
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search patients, jump to a section…"
            className="min-h-11 flex-1 bg-transparent py-3 text-sm outline-none"
          />
        </div>
        <div className="max-h-[min(60dvh,420px)] overflow-y-auto p-2">
          {filteredStatic.map((cmd, i) => (
            <motion.button
              key={cmd.id}
              type="button"
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm hover:bg-secondary native-press"
              onClick={() => {
                cmd.run();
                onClose();
              }}
              initial={reducedMotion ? false : { opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: listItemDelay(i, !!reducedMotion) }}
            >
              {cmd.label}
            </motion.button>
          ))}
          {(data?.items ?? []).map((patient, i) => (
            <motion.button
              key={patient.id}
              type="button"
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm hover:bg-secondary native-press"
              onClick={() => {
                navigate({
                  to: "/dashboard/patients/$patientId",
                  params: { patientId: patient.id },
                });
                onClose();
              }}
              initial={reducedMotion ? false : { opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                delay: listItemDelay(
                  i + filteredStatic.length,
                  !!reducedMotion,
                ),
              }}
            >
              <User className="size-4 shrink-0 text-muted-foreground" />
              <span className="truncate">{patient.full_name}</span>
            </motion.button>
          ))}
          {isFetching ? (
            <p className="px-3 py-2 text-xs text-muted-foreground">
              Searching…
            </p>
          ) : null}
        </div>
      </ResponsiveModalContent>
    </ResponsiveModal>
  );
}

export function useCommandPalette() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  return { open, setOpen };
}
