import { API_BASE_URL, readErrorMessage, requestJson } from "./client";
import type { SearchResponse, StreamEvent } from "./types";

export function searchKnowledgeBase(payload: {
  knowledge_base_id: number;
  query: string;
  top_k: number;
}): Promise<SearchResponse> {
  return requestJson<SearchResponse>("/api/search", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function streamSearchKnowledgeBase(
  payload: { knowledge_base_id: number; query: string; top_k: number },
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/search/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  if (!response.body) {
    throw new Error("浏览器不支持流式响应");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";

    for (const event of events) {
      const line = event.split("\n").find((entry) => entry.startsWith("data: "));
      if (!line) {
        continue;
      }
      onEvent(JSON.parse(line.slice(6)) as StreamEvent);
    }
  }
}

