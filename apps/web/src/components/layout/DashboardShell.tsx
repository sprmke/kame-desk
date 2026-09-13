import { useEffect, useState } from "react";
import { useNavigate, useRouterState } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { clearAuth, isImpersonating, setActiveClinic } from "@/lib/auth";
import { defaultLandingPath, type ClinicRole } from "@/lib/rbac";
import { useSession } from "@/hooks/useSession";
import { CommandPalette, useCommandPalette } from "@/components/CommandPalette";
import { AssistantLauncher } from "@/features/assistant/components/AssistantLauncher";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { AppHeader } from "@/components/layout/AppHeader";
import { PageTransition } from "@/components/layout/PageTransition";
import { SidebarProvider } from "@/components/layout/SidebarContext";
import { RealtimeProvider } from "@/features/waiting-room/context/RealtimeContext";
import {
  bottomTabActiveKey,
  bottomTabLeaves,
  pageTransitionKey,
} from "@/components/layout/nav-config";
import {
  BottomTabBar,
  aboveBottomTabBarClassName,
  bottomTabBarOffsetClassName,
  moreTabItem,
} from "@/components/mobile/BottomTabBar";
import { MobileMoreSheet } from "@/components/mobile/MobileMoreSheet";
import { ConnectivityBanner } from "@/components/layout/ConnectivityBanner";
import { useOfflineSoapSync } from "@/lib/offlineSoapSync";
import { cn } from "@/lib/utils";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const { open, setOpen } = useCommandPalette();
  const [moreOpen, setMoreOpen] = useState(false);
  const [membershipLost, setMembershipLost] = useState(false);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { memberships } = useSession();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const tabActiveKey = moreOpen ? "more" : bottomTabActiveKey(pathname);
  const supportLogin = isImpersonating();
  useOfflineSoapSync();

  useEffect(() => {
    function onMembershipLost() {
      setMembershipLost(true);
    }
    window.addEventListener("doctordesk:membership-lost", onMembershipLost);
    return () =>
      window.removeEventListener(
        "doctordesk:membership-lost",
        onMembershipLost,
      );
  }, []);

  return (
    <SidebarProvider>
      <RealtimeProvider>
        <div className="flex h-screen overflow-hidden bg-background">
          <AppSidebar />
          <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
            <ConnectivityBanner />
            {membershipLost && memberships.length > 0 ? (
              <div className="flex flex-wrap items-center justify-between gap-3 bg-warning-100 px-4 py-2 text-sm text-warning-900">
                <span>
                  Clinic access changed. Switch workspace to continue.
                </span>
                <select
                  className="rounded border border-warning-900/20 bg-card px-2 py-1 text-sm"
                  defaultValue=""
                  onChange={(e) => {
                    const next = e.target.value;
                    if (!next) return;
                    setActiveClinic(next);
                    qc.clear();
                    setMembershipLost(false);
                    const role = memberships.find((m) => m.clinic_id === next)
                      ?.role as ClinicRole | undefined;
                    navigate({ to: defaultLandingPath(role) });
                  }}
                >
                  <option value="" disabled>
                    Choose clinic
                  </option>
                  {memberships.map((m) => (
                    <option key={m.clinic_id} value={m.clinic_id}>
                      {m.clinic_name}
                    </option>
                  ))}
                </select>
              </div>
            ) : null}
            {supportLogin ? (
              <div className="flex items-center justify-between gap-3 bg-warning-100 px-4 py-2 text-sm text-warning-900">
                <span>Support login. Changes are audited.</span>
                <button
                  type="button"
                  className="font-medium underline"
                  onClick={() => {
                    clearAuth();
                    navigate({ to: "/platform" });
                  }}
                >
                  Exit
                </button>
              </div>
            ) : null}
            <AppHeader onOpenSearch={() => setOpen(true)} />
            <main
              className={cn(
                // Reserve the scrollbar gutter so centered page containers do
                // not shift horizontally between short and long pages.
                "flex-1 overflow-y-auto p-4 [scrollbar-gutter:stable] sm:p-6",
                bottomTabBarOffsetClassName(),
              )}
            >
              <PageTransition transitionKey={pageTransitionKey(pathname)}>
                {children}
              </PageTransition>
            </main>
          </div>
        </div>
        <BottomTabBar
          activeKey={tabActiveKey}
          items={[
            {
              key: "calendar",
              label: "Calendar",
              to: "/dashboard/appointments",
              Icon: bottomTabLeaves[0].icon,
            },
            {
              key: "waiting",
              label: "Waiting",
              to: "/dashboard/waiting-room",
              Icon: bottomTabLeaves[1].icon,
            },
            {
              key: "patients",
              label: "Patients",
              to: "/dashboard/patients",
              Icon: bottomTabLeaves[2].icon,
            },
            moreTabItem(() => setMoreOpen(true)),
          ]}
        />
        <MobileMoreSheet open={moreOpen} onOpenChange={setMoreOpen} />
        <CommandPalette open={open} onClose={() => setOpen(false)} />
        <AssistantLauncher className={aboveBottomTabBarClassName()} />
      </RealtimeProvider>
    </SidebarProvider>
  );
}
