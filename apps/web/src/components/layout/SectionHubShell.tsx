import { useState } from "react";
import { PageContainer } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { SectionSubNav } from "@/components/layout/SectionSubNav";
import { SectionActionsProvider } from "@/components/layout/SectionHubContext";
import type { SectionHub } from "@/components/layout/nav-config";
import { useSession } from "@/hooks/useSession";

type Props = {
  hub: SectionHub;
  children: React.ReactNode;
};

/**
 * Chrome for a tabbed section. Owns the container and the only page heading, so
 * the title stays fixed while tabs swap the content below them.
 * Tab pages render content plus, optionally, `SectionHeaderActions`.
 */
export function SectionHubShell({ hub, children }: Props) {
  const { can } = useSession();
  const [actionsSlot, setActionsSlot] = useState<HTMLDivElement | null>(null);

  return (
    <PageContainer>
      <PageHeader
        title={hub.title}
        actions={
          <div
            ref={setActionsSlot}
            className="flex flex-wrap items-center gap-2"
          />
        }
        subNav={<SectionSubNav tabs={hub.tabs} can={can} label={hub.title} />}
      />
      <SectionActionsProvider value={actionsSlot}>
        {children}
      </SectionActionsProvider>
    </PageContainer>
  );
}
