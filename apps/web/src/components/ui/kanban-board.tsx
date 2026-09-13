import * as React from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  TouchSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { useDraggable, useDroppable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { cn } from "@/lib/utils";

export type KanbanColumn<T> = {
  id: string;
  title: React.ReactNode;
  items: T[];
};

type KanbanBoardProps<T> = {
  columns: KanbanColumn<T>[];
  getItemId: (item: T) => string;
  getItemColumnId: (item: T) => string;
  renderItem: (item: T, state: { isDragging: boolean }) => React.ReactNode;
  onMove: (itemId: string, fromColumnId: string, toColumnId: string) => void;
  canDrop?: (
    itemId: string,
    fromColumnId: string,
    toColumnId: string,
  ) => boolean;
  disabled?: boolean;
  className?: string;
};

function KanbanCardShell({
  id,
  disabled,
  children,
}: {
  id: string;
  disabled?: boolean;
  children: React.ReactNode;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({ id, disabled });

  const style = transform
    ? { transform: CSS.Translate.toString(transform) }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        "touch-manipulation",
        isDragging && "opacity-40",
        !disabled && "cursor-grab active:cursor-grabbing",
      )}
      {...listeners}
      {...attributes}
    >
      {children}
    </div>
  );
}

function KanbanColumnShell({
  id,
  title,
  count,
  children,
  isOver,
  canAccept,
}: {
  id: string;
  title: React.ReactNode;
  count: number;
  children: React.ReactNode;
  isOver: boolean;
  canAccept: boolean;
}) {
  const { setNodeRef } = useDroppable({ id });

  return (
    <section
      ref={setNodeRef}
      className={cn(
        "flex min-w-0 flex-1 flex-col gap-2.5 rounded-2xl border border-border bg-secondary/30 p-3 lg:min-w-[240px]",
        isOver && canAccept && "ring-2 ring-primary/40",
        isOver && !canAccept && "ring-2 ring-destructive/30",
      )}
    >
      <header className="flex items-center justify-between px-1 text-sm font-medium text-foreground">
        <span>{title}</span>
        <span className="rounded-md border border-border px-2 py-0.5 text-xs text-muted-foreground">
          {count}
        </span>
      </header>
      <div className="flex flex-col gap-2">{children}</div>
    </section>
  );
}

export function KanbanBoard<T>({
  columns,
  getItemId,
  getItemColumnId,
  renderItem,
  onMove,
  canDrop,
  disabled = false,
  className,
}: KanbanBoardProps<T>) {
  const [activeId, setActiveId] = React.useState<string | null>(null);
  const [overColumnId, setOverColumnId] = React.useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(TouchSensor, {
      activationConstraint: { delay: 180, tolerance: 6 },
    }),
  );

  const itemById = React.useMemo(() => {
    const map = new Map<string, T>();
    for (const col of columns) {
      for (const item of col.items) {
        map.set(getItemId(item), item);
      }
    }
    return map;
  }, [columns, getItemId]);

  const columnIds = new Set(columns.map((c) => c.id));
  const activeItem = activeId ? itemById.get(activeId) : undefined;

  function resolveColumnId(overId: string | null | undefined) {
    if (!overId) return null;
    if (columnIds.has(overId)) return overId;
    const item = itemById.get(overId);
    return item ? getItemColumnId(item) : null;
  }

  function handleDragStart(event: DragStartEvent) {
    setActiveId(String(event.active.id));
  }

  function handleDragEnd(event: DragEndEvent) {
    const itemId = String(event.active.id);
    const item = itemById.get(itemId);
    if (!item) {
      setActiveId(null);
      setOverColumnId(null);
      return;
    }
    const fromColumnId = getItemColumnId(item);
    const toColumnId = resolveColumnId(
      event.over?.id ? String(event.over.id) : null,
    );
    setActiveId(null);
    setOverColumnId(null);
    if (!toColumnId || toColumnId === fromColumnId) return;
    if (canDrop && !canDrop(itemId, fromColumnId, toColumnId)) return;
    onMove(itemId, fromColumnId, toColumnId);
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragOver={(event) => {
        setOverColumnId(
          resolveColumnId(event.over?.id ? String(event.over.id) : null),
        );
      }}
      onDragCancel={() => {
        setActiveId(null);
        setOverColumnId(null);
      }}
    >
      <div className={cn("flex gap-3 overflow-x-auto pb-2", className)}>
        {columns.map((column) => (
          <KanbanColumnShell
            key={column.id}
            id={column.id}
            title={column.title}
            count={column.items.length}
            isOver={overColumnId === column.id}
            canAccept={
              activeId
                ? (canDrop?.(
                    activeId,
                    getItemColumnId(itemById.get(activeId)!),
                    column.id,
                  ) ?? true)
                : false
            }
          >
            {column.items.length === 0 ? (
              <p className="py-6 text-center text-xs text-muted-foreground">
                Empty
              </p>
            ) : (
              column.items.map((item) => {
                const id = getItemId(item);
                return (
                  <KanbanCardShell key={id} id={id} disabled={disabled}>
                    {renderItem(item, { isDragging: activeId === id })}
                  </KanbanCardShell>
                );
              })
            )}
          </KanbanColumnShell>
        ))}
      </div>
      <DragOverlay>
        {activeItem ? (
          <div className="cursor-grabbing opacity-95 shadow-theme-md">
            {renderItem(activeItem, { isDragging: true })}
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
