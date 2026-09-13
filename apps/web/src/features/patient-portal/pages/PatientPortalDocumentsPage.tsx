import { useMutation, useQuery } from "@tanstack/react-query";
import { FileText, Download } from "lucide-react";
import { PatientPortalAppShell } from "@/features/patient-portal/components/PatientPortalAppShell";
import { patientPortalApi } from "@/features/patient-portal/lib/patientPortalClient";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState, SectionCard } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";

export function PatientPortalDocumentsPage({ slug }: { slug: string }) {
  const me = useQuery({
    queryKey: ["portal-me"],
    queryFn: patientPortalApi.getMe,
  });
  const documents = useQuery({
    queryKey: ["portal-documents"],
    queryFn: patientPortalApi.getDocuments,
  });

  const download = useMutation({
    mutationFn: (fileId: string) =>
      patientPortalApi.getDocumentDownloadUrl(fileId),
    onSuccess: (data) => {
      window.open(data.download_url, "_blank", "noopener,noreferrer");
    },
  });

  return (
    <PatientPortalAppShell
      slug={slug}
      clinicName={me.data?.clinic_name}
      patientName={me.data?.full_name}
    >
      <h1 className="mb-4 text-lg font-semibold text-foreground">Documents</h1>

      {documents.isLoading ? (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : documents.isError ? (
        <SectionCard>
          <ErrorState
            heading="Could not load your documents"
            onRetry={() => documents.refetch()}
          />
        </SectionCard>
      ) : documents.data && documents.data.length > 0 ? (
        <div className="flex flex-col gap-3">
          {documents.data.map((doc) => (
            <Card key={doc.id}>
              <CardContent className="flex items-center justify-between gap-3 py-4">
                <div className="flex items-center gap-3">
                  <FileText
                    className="size-5 shrink-0 text-muted-foreground"
                    aria-hidden
                  />
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {doc.description ?? doc.file_type.replace("_", " ")}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(doc.uploaded_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={download.isPending}
                  onClick={() => download.mutate(doc.id)}
                >
                  <Download className="size-4" aria-hidden />
                  Download
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <SectionCard>
          <EmptyState
            icon={FileText}
            heading="No documents yet"
            description="Lab results and other files your clinic shares will appear here."
          />
        </SectionCard>
      )}
    </PatientPortalAppShell>
  );
}
