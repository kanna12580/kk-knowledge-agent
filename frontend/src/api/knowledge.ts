import { requestJson } from "./client";
import type { KnowledgeBase, Page } from "./types";

export function listKnowledgeBases(page = 1, pageSize = 20): Promise<Page<KnowledgeBase>> {
  return requestJson<Page<KnowledgeBase>>(`/api/knowledge-bases?page=${page}&page_size=${pageSize}`);
}

export function createKnowledgeBase(payload: {
  name: string;
  description?: string;
}): Promise<KnowledgeBase> {
  return requestJson<KnowledgeBase>("/api/knowledge-bases", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

