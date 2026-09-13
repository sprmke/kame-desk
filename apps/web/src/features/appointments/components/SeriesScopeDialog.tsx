import { Button } from "@/components/ui/button";
import {
  ResponsiveModal,
  ResponsiveModalContent,
  ResponsiveModalHeader,
  ResponsiveModalTitle,
} from "@/components/ui/responsive-modal";

export type SeriesScope = "this" | "following" | "all";

type Props = {
  open: boolean;
  action: "cancel" | "edit";
  hasSeries: boolean;
  onChoose: (scope: SeriesScope) => void;
  onClose: () => void;
};

export function SeriesScopeDialog({ open, action, onChoose, onClose }: Props) {
  const verb = action === "cancel" ? "Cancel" : "Edit";

  return (
    <ResponsiveModal open={open} onOpenChange={(next) => !next && onClose()}>
      <ResponsiveModalContent className="max-w-sm">
        <ResponsiveModalHeader>
          <ResponsiveModalTitle>
            {verb} recurring appointment
          </ResponsiveModalTitle>
        </ResponsiveModalHeader>
        <div className="flex flex-col gap-2">
          <Button
            variant="outline"
            className="min-h-[44px]"
            onClick={() => onChoose("this")}
          >
            This event
          </Button>
          <Button
            variant="outline"
            className="min-h-[44px]"
            onClick={() => onChoose("following")}
          >
            This and following
          </Button>
          <Button
            variant="outline"
            className="min-h-[44px]"
            onClick={() => onChoose("all")}
          >
            All events
          </Button>
        </div>
      </ResponsiveModalContent>
    </ResponsiveModal>
  );
}
