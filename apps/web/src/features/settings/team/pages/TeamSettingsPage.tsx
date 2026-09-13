import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Mail, UserPlus, Users, X } from "lucide-react";
import { api } from "@/lib/apiClient";
import { getClinicId } from "@/lib/auth";
import { PageHeader } from "@/components/layout/PageHeader";
import { SettingsSection } from "@/components/settings/SettingsSection";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState, SectionCard } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { TeamSettingsSkeleton } from "@/components/skeletons/PageSkeletons";
import { EntityList, EntityRow } from "@/components/ui/entity-row";
import { InviteTeammateModal } from "@/features/settings/team/components/InviteTeammateModal";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const ROLE_LABEL: Record<string, string> = {
  owner: "Owner",
  admin: "Admin",
  doctor: "Doctor",
  reception: "Reception",
};

export function TeamSettingsPage() {
  const clinicId = getClinicId()!;
  const qc = useQueryClient();
  const [inviteOpen, setInviteOpen] = useState(false);
  const {
    data: members,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["members", clinicId],
    queryFn: () => api.listMembers(clinicId),
  });
  const { data: invitations } = useQuery({
    queryKey: ["invitations", clinicId],
    queryFn: () => api.listInvitations(clinicId),
  });
  const { data: seats } = useQuery({
    queryKey: ["seat-summary", clinicId],
    queryFn: () => api.getSeatSummary(clinicId),
  });

  const patchMember = useMutation({
    mutationFn: ({
      membershipId,
      body,
    }: {
      membershipId: string;
      body: { role?: string; is_active?: boolean };
    }) => api.patchMember(clinicId, membershipId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["members", clinicId] }),
  });

  const revokeInvite = useMutation({
    mutationFn: (invitationId: string) =>
      api.revokeInvitation(clinicId, invitationId),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["invitations", clinicId] }),
  });

  const resendInvite = useMutation({
    mutationFn: (invitationId: string) =>
      api.resendInvitation(clinicId, invitationId),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["invitations", clinicId] }),
  });

  const pendingInvites = (invitations ?? []).filter(
    (i) => !i.accepted_at && !i.revoked_at,
  );

  return (
    <div>
      <PageHeader
        title="Team"
        actions={
          <Button type="button" onClick={() => setInviteOpen(true)}>
            <UserPlus className="size-4" />
            Invite
          </Button>
        }
      />

      {seats?.limit != null ? (
        <p className="mb-4 text-sm text-muted-foreground">
          Doctor seats: {seats.used} of {seats.limit} used
          {seats.remaining === 0 ? " (limit reached)" : ""}
        </p>
      ) : null}

      {pendingInvites.length > 0 && (
        <SettingsSection title="Pending invites" divided={false}>
          <SectionCard>
            <div className="flex flex-col gap-1">
              {pendingInvites.map((i) => (
                <div
                  key={i.id}
                  className="flex items-center justify-between gap-2 rounded-lg px-2 py-2 text-sm"
                >
                  <span className="text-foreground">
                    {i.email}{" "}
                    <span className="text-muted-foreground">
                      · {ROLE_LABEL[i.role] ?? i.role}
                    </span>
                  </span>
                  <div className="flex items-center gap-1">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => resendInvite.mutate(i.id)}
                      disabled={resendInvite.isPending}
                    >
                      <Mail className="size-4" />
                      Resend
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="size-8 text-destructive hover:text-destructive"
                      onClick={() => revokeInvite.mutate(i.id)}
                      aria-label="Revoke invite"
                    >
                      <X className="size-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </SettingsSection>
      )}

      <SettingsSection title="Members" divided={false}>
        <SectionCard>
          {isLoading ? (
            <TeamSettingsSkeleton />
          ) : isError ? (
            <ErrorState onRetry={() => refetch()} />
          ) : (members ?? []).length === 0 ? (
            <EmptyState
              icon={Users}
              heading="No members yet"
              size="sm"
              action={
                <Button type="button" onClick={() => setInviteOpen(true)}>
                  Invite
                </Button>
              }
            />
          ) : (
            <EntityList>
              {(members ?? []).map((m) => (
                <li key={m.id} className="px-2">
                  <EntityRow
                    title={m.full_name}
                    subtitle={m.email}
                    trailing={
                      <div className="flex items-center gap-2">
                        {!m.is_active && (
                          <Badge variant="warning">Inactive</Badge>
                        )}
                        <Select
                          value={m.role}
                          disabled={!m.is_active}
                          onValueChange={(role) =>
                            patchMember.mutate({
                              membershipId: m.id,
                              body: { role },
                            })
                          }
                        >
                          <SelectTrigger className="h-8 w-[110px]">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="owner">Owner</SelectItem>
                            <SelectItem value="admin">Admin</SelectItem>
                            <SelectItem value="doctor">Doctor</SelectItem>
                            <SelectItem value="reception">Reception</SelectItem>
                          </SelectContent>
                        </Select>
                        {m.is_active && m.role !== "owner" && (
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            className="text-destructive hover:text-destructive"
                            onClick={() =>
                              patchMember.mutate({
                                membershipId: m.id,
                                body: { is_active: false },
                              })
                            }
                          >
                            Deactivate
                          </Button>
                        )}
                      </div>
                    }
                  />
                </li>
              ))}
            </EntityList>
          )}
        </SectionCard>
      </SettingsSection>

      <InviteTeammateModal
        clinicId={clinicId}
        open={inviteOpen}
        onOpenChange={setInviteOpen}
      />
    </div>
  );
}
