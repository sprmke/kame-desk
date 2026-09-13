export type AssistantSseEvent =
  | { type: "text"; content: string }
  | {
      type: "tool_result";
      tool: string;
      tier: number;
      result: Record<string, unknown>;
    }
  | {
      type: "confirm_card";
      action_id: string;
      tool: string;
      tier: number;
      proposal: Record<string, unknown>;
      external_send?: boolean;
    }
  | { type: "done" }
  | { type: "error"; message: string };

export function parseAssistantSseChunk(buffer: string): {
  events: AssistantSseEvent[];
  remainder: string;
} {
  const events: AssistantSseEvent[] = [];
  const parts = buffer.split("\n\n");
  const remainder = parts.pop() ?? "";
  for (const part of parts) {
    const line = part.split("\n").find((row) => row.startsWith("data: "));
    if (!line) continue;
    try {
      events.push(JSON.parse(line.slice(6)) as AssistantSseEvent);
    } catch {
      // ignore malformed chunk
    }
  }
  return { events, remainder };
}
