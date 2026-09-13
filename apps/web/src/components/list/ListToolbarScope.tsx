import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useId,
  useMemo,
  useState,
  type ReactNode,
} from "react";

type ToolbarMenuContextValue = {
  openId: string | null;
  setOpenId: (id: string | null) => void;
};

const ToolbarMenuContext = createContext<ToolbarMenuContextValue | null>(null);

export function ListToolbarScope({ children }: { children: ReactNode }) {
  const [openId, setOpenId] = useState<string | null>(null);
  const value = useMemo(() => ({ openId, setOpenId }), [openId]);
  return (
    <ToolbarMenuContext.Provider value={value}>
      {children}
    </ToolbarMenuContext.Provider>
  );
}

type SetOpen = (next: boolean | ((prev: boolean) => boolean)) => void;

export function useListToolbarMenuOpen(stableKey?: string): [boolean, SetOpen] {
  const ctx = useContext(ToolbarMenuContext);
  const reactId = useId();
  const id = stableKey ?? reactId;
  const [localOpen, setLocalOpen] = useState(false);
  const useScope = Boolean(ctx);
  const open = useScope ? ctx!.openId === id : localOpen;

  const setOpen = useCallback<SetOpen>(
    (next) => {
      if (!useScope) {
        setLocalOpen(next);
        return;
      }
      const prev = ctx!.openId === id;
      const value = typeof next === "function" ? next(prev) : next;
      if (value) ctx!.setOpenId(id);
      else if (ctx!.openId === id) ctx!.setOpenId(null);
    },
    [ctx, id, useScope],
  );

  return [open, setOpen];
}

export function useClaimToolbarMenu(
  open: boolean,
  onOpenChange: (open: boolean) => void,
  stableKey?: string,
): { open: boolean; onOpenChange: (open: boolean) => void } {
  const [mine, setMine] = useListToolbarMenuOpen(stableKey);
  const inScope = useContext(ToolbarMenuContext) != null;

  useEffect(() => {
    if (!inScope) return;
    if (open) setMine(true);
  }, [inScope, open, setMine]);

  useEffect(() => {
    if (!inScope) return;
    if (open && !mine) onOpenChange(false);
  }, [inScope, mine, open, onOpenChange]);

  const handleOpenChange = useCallback(
    (next: boolean) => {
      setMine(next);
      onOpenChange(next);
    },
    [onOpenChange, setMine],
  );

  return {
    open: inScope ? open && mine : open,
    onOpenChange: handleOpenChange,
  };
}
