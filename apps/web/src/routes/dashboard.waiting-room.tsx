import { createFileRoute } from "@tanstack/react-router";
import { WaitingRoomPage } from "@/features/waiting-room/pages/WaitingRoomPage";
import { useRealtimeState } from "@/features/waiting-room/context/RealtimeContext";

export const Route = createFileRoute("/dashboard/waiting-room")({
  component: WaitingRoomRoute,
});

function WaitingRoomRoute() {
  const connectionState = useRealtimeState();
  return <WaitingRoomPage connectionState={connectionState} />;
}
