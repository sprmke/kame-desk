import { KanbanBoard } from "@/components/ui/kanban-board";
import { WaitingRoomCard } from "./WaitingRoomBoard";
import {
  canDropToColumn,
  columnForItem,
  columnToVisitStatus,
  type VisitColumn,
  type WaitingRoomItem,
} from "../lib/waitingRoom";
import { sortArrivedByLongestWait } from "../lib/waitTime";

const COLUMN_ORDER: VisitColumn[] = [
  "Scheduled",
  "Arrived",
  "In Consultation",
  "Completed",
];

const COLUMN_LABELS: Record<VisitColumn, string> = {
  Scheduled: "Scheduled",
  Arrived: "Arrived",
  "In Consultation": "In consultation",
  Completed: "Completed",
};

type Props = {
  items: WaitingRoomItem[];
  onAdvance: (
    id: string,
    status: "Arrived" | "In Consultation" | "Completed",
  ) => void;
  pendingId: string | null;
  now?: Date;
};

export function WaitingRoomKanban({ items, onAdvance, pendingId, now }: Props) {
  const clock = now ?? new Date();
  const columns = COLUMN_ORDER.map((id) => {
    const columnItems = items.filter((item) => columnForItem(item) === id);
    return {
      id,
      title: COLUMN_LABELS[id],
      items:
        id === "Arrived"
          ? sortArrivedByLongestWait(columnItems, clock)
          : columnItems,
    };
  });

  return (
    <KanbanBoard
      columns={columns}
      getItemId={(item) => item.id}
      getItemColumnId={(item) => columnForItem(item)}
      disabled={Boolean(pendingId)}
      canDrop={(itemId, _fromColumnId, toColumnId) => {
        const item = items.find((row) => row.id === itemId);
        if (!item) return false;
        return canDropToColumn(
          item.current_visit_status,
          toColumnId as VisitColumn,
        );
      }}
      onMove={(itemId, _fromColumnId, toColumnId) => {
        const target = columnToVisitStatus(toColumnId as VisitColumn);
        if (!target) return;
        onAdvance(itemId, target);
      }}
      renderItem={(item) => (
        <WaitingRoomCard
          item={item}
          onAdvance={onAdvance}
          pendingId={pendingId}
          now={clock}
        />
      )}
    />
  );
}
