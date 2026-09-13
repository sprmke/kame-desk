import { Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Rows3, UserPlus } from "lucide-react";
import { ConnectionIndicator } from "../components/ConnectionIndicator";
import { DoctorFilterBar } from "../components/DoctorFilterBar";
import { WalkInDialog } from "../components/WalkInDialog";
import {
  WaitingRoomColumn,
  filterActiveWaiting,
} from "../components/WaitingRoomBoard";
import { WaitingRoomKanban } from "../components/WaitingRoomKanban";
import {
  groupByColumn,
  useAdvanceVisitStatus,
  useWaitingRoom,
} from "../hooks/useWaitingRoom";
import {
  doctorsFromQueue,
  filterByDoctor,
  useLiveTimer,
} from "../lib/waitTime";
import type { WsConnectionState } from "@/lib/websocket";
import { PageContainer } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SegmentedControl } from "@/components/ui/sliding-tabs";
import { EmptyState, SectionCard } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import {
  WaitingRoomMobileSkeleton,
  WaitingRoomSkeleton,
} from "@/components/skeletons/PageSkeletons";
import { useIsBelowLg } from "@/hooks/useMediaQuery";

const MOBILE_COLUMNS = [
  { value: "Scheduled", label: "Scheduled" },
  { value: "Arrived", label: "Arrived" },
  { value: "In Consultation", label: "In consult" },
  { value: "Completed", label: "Done" },
] as const;

const DOCTOR_FILTER_KEY = "dd-waiting-room-doctor";

type MobileColumn = (typeof MOBILE_COLUMNS)[number]["value"];

type Props = {
  connectionState: WsConnectionState;
  compact?: boolean;
};

function readSavedDoctorFilter(): string | "all" {
  if (typeof window === "undefined") return "all";
  return localStorage.getItem(DOCTOR_FILTER_KEY) ?? "all";
}

export function WaitingRoomPage({ connectionState }: Props) {
  const { data, isLoading, isError, refetch } = useWaitingRoom();
  const advance = useAdvanceVisitStatus();
  const queryClient = useQueryClient();
  const now = useLiveTimer(15000);

  const [pendingId, setPendingId] = useState<string | null>(null);
  const [showWalkIn, setShowWalkIn] = useState(false);
  const [mobileColumn, setMobileColumn] = useState<MobileColumn>("Scheduled");
  const [doctorFilter, setDoctorFilter] = useState<string | "all">(
    readSavedDoctorFilter,
  );
  const isBelowLg = useIsBelowLg();

  const allItems = data?.items ?? [];
  const doctors = useMemo(() => doctorsFromQueue(allItems), [allItems]);
  const activeDoctorFilter =
    doctorFilter !== "all" && doctors.some((d) => d.id === doctorFilter)
      ? doctorFilter
      : "all";
  const filteredItems = useMemo(
    () => filterByDoctor(allItems, activeDoctorFilter),
    [allItems, activeDoctorFilter],
  );
  const columns = groupByColumn(filteredItems);

  function handleDoctorFilter(next: string | "all") {
    setDoctorFilter(next);
    if (typeof window !== "undefined") {
      localStorage.setItem(DOCTOR_FILTER_KEY, next);
    }
  }

  async function handleAdvance(
    id: string,
    status: "Arrived" | "In Consultation" | "Completed",
  ) {
    setPendingId(id);
    try {
      await advance.mutateAsync({ appointmentId: id, visitStatus: status });
    } finally {
      setPendingId(null);
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title="Waiting room"
        actions={
          <>
            <ConnectionIndicator state={connectionState} />
            <Button variant="outline" onClick={() => setShowWalkIn(true)}>
              <UserPlus className="size-4" />
              Walk-in
            </Button>
          </>
        }
      />

      <WalkInDialog
        open={showWalkIn}
        onOpenChange={setShowWalkIn}
        onDone={() => {
          setShowWalkIn(false);
          queryClient.invalidateQueries({ queryKey: ["waiting-room"] });
        }}
      />

      {isLoading ? (
        isBelowLg ? (
          <WaitingRoomMobileSkeleton />
        ) : (
          <WaitingRoomSkeleton />
        )
      ) : isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : (
        <div className="flex flex-col gap-3">
          <DoctorFilterBar
            doctors={doctors}
            totalCount={allItems.length}
            value={activeDoctorFilter}
            onChange={handleDoctorFilter}
          />

          {isBelowLg ? (
            <div className="flex flex-col gap-3">
              <SegmentedControl
                value={mobileColumn}
                onChange={setMobileColumn}
                options={[...MOBILE_COLUMNS]}
                size="compact"
                fullWidth
                equalSegments
                aria-label="Visit status"
              />
              {columns[mobileColumn].length === 0 ? (
                <SectionCard>
                  <EmptyState icon={Rows3} heading="No patients" size="sm" />
                </SectionCard>
              ) : (
                <WaitingRoomColumn
                  title={mobileColumn}
                  items={columns[mobileColumn]}
                  onAdvance={handleAdvance}
                  pendingId={pendingId}
                  swipeActions
                  now={now}
                />
              )}
            </div>
          ) : (
            <WaitingRoomKanban
              items={filteredItems}
              onAdvance={handleAdvance}
              pendingId={pendingId}
              now={now}
            />
          )}
        </div>
      )}
    </PageContainer>
  );
}

export function WaitingPatientsWidget({ connectionState }: Props) {
  const { data } = useWaitingRoom();
  const active = filterActiveWaiting(data?.items ?? []).slice(0, 5);

  return (
    <Card>
      <CardContent className="pt-5">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="font-medium text-foreground">Waiting patients</h2>
          <div className="flex items-center gap-3">
            <ConnectionIndicator state={connectionState} />
            <Link
              to="/dashboard/waiting-room"
              className="text-sm font-medium text-primary hover:underline"
            >
              Open
            </Link>
          </div>
        </div>
        {active.length === 0 ? (
          <EmptyState icon={Rows3} heading="No patients waiting" size="sm" />
        ) : (
          <ul className="flex flex-col divide-y divide-border text-sm">
            {active.map((item) => (
              <li
                key={item.id}
                className="flex justify-between py-2 first:pt-0 last:pb-0"
              >
                <span className="text-foreground">
                  {item.patient_name ?? "Patient"}
                </span>
                <span className="text-muted-foreground">
                  {item.current_visit_status ?? "Scheduled"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
