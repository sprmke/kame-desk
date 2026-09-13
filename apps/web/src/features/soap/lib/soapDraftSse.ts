export type SoapDraftSseEvent =
  | { type: "field"; field: string; value: string }
  | { type: "done" }
  | { type: "error"; message: string };

export function parseSseChunk(buffer: string): {
  events: SoapDraftSseEvent[];
  remainder: string;
} {
  const events: SoapDraftSseEvent[] = [];
  const parts = buffer.split("\n\n");
  const remainder = parts.pop() ?? "";

  for (const part of parts) {
    const line = part.split("\n").find((row) => row.startsWith("data: "));
    if (!line) continue;
    try {
      events.push(JSON.parse(line.slice(6)) as SoapDraftSseEvent);
    } catch {
      // ignore malformed chunks until the stream completes
    }
  }

  return { events, remainder };
}

export function applySoapDraftField(
  current: Record<string, string>,
  field: string,
  value: string,
): Record<string, string> {
  if (!field) return current;
  return { ...current, [field]: value };
}
