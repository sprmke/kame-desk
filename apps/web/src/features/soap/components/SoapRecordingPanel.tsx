import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Mic, Square } from "lucide-react";
import { api } from "@/lib/apiClient";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type Props = {
  appointmentId: string;
  disabled?: boolean;
  onUseTranscript: (text: string) => void;
};

export function SoapRecordingPanel({
  appointmentId,
  disabled,
  onUseTranscript,
}: Props) {
  const qc = useQueryClient();
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const { data: recordings } = useQuery({
    queryKey: ["recordings", appointmentId],
    queryFn: () => api.listRecordings(appointmentId),
    refetchInterval: (query) => {
      const rows = query.state.data ?? [];
      const active = rows.some((r) =>
        ["pending", "processing"].includes(r.transcription_status),
      );
      return active ? 3000 : false;
    },
  });

  const latest = recordings?.[0];

  const uploadRecording = useMutation({
    mutationFn: async (blob: Blob) => {
      const contentType = blob.type || "audio/webm";
      const created = await api.createRecordingUpload(appointmentId, {
        content_type: contentType,
        file_size_bytes: blob.size,
      });
      const put = await fetch(created.upload_url, {
        method: "PUT",
        headers: { "Content-Type": contentType },
        body: blob,
      });
      if (!put.ok) throw new Error("Upload failed");
      await api.submitRecording(appointmentId, created.recording.id);
      return created.recording.id;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["recordings", appointmentId] });
    },
    onError: () => setError("Recording failed"),
  });

  useEffect(() => {
    return () => {
      mediaRecorderRef.current?.stream.getTracks().forEach((t) => t.stop());
    };
  }, []);

  async function startRecording() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });
        if (blob.size > 0) {
          await uploadRecording.mutateAsync(blob);
        }
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch {
      setError("Microphone unavailable");
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  }

  const status = latest?.transcription_status;
  const busy = recording || uploadRecording.isPending;

  return (
    <Card>
      <CardContent className="pt-5">
        <div className="flex flex-wrap items-center gap-2">
          {!recording ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={disabled || busy}
              onClick={() => startRecording()}
            >
              <Mic className="size-4" />
              Record
            </Button>
          ) : (
            <Button type="button" size="sm" onClick={() => stopRecording()}>
              <Square className="size-4" />
              Stop
            </Button>
          )}
          {status === "processing" && (
            <span className="text-sm text-muted-foreground">Transcribing…</span>
          )}
          {status === "failed" && (
            <span className="text-sm text-destructive">
              Transcription failed
            </span>
          )}
          {status === "done" && latest?.transcript_text && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={disabled}
              onClick={() => onUseTranscript(latest.transcript_text!)}
            >
              Use transcript
            </Button>
          )}
        </div>
        {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
      </CardContent>
    </Card>
  );
}
