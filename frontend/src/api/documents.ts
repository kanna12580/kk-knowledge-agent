import { requestForm, requestJson } from "./client";
import type { KnowledgeDocument, KnowledgeDocumentDetail, Page } from "./types";

export function listDocuments(
  knowledgeBaseId: number,
  page = 1,
  pageSize = 10,
): Promise<Page<KnowledgeDocument>> {
  return requestJson<Page<KnowledgeDocument>>(
    `/api/knowledge-bases/${knowledgeBaseId}/documents?page=${page}&page_size=${pageSize}`,
  );
}

export function uploadTextDocument(
  knowledgeBaseId: number,
  payload: { title: string; content: string },
): Promise<KnowledgeDocumentDetail> {
  return requestJson<KnowledgeDocumentDetail>(`/api/knowledge-bases/${knowledgeBaseId}/documents/text`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function uploadTxtDocument(
  knowledgeBaseId: number,
  title: string,
  file: File,
): Promise<KnowledgeDocumentDetail> {
  const formData = new FormData();
  formData.append("title", title);
  formData.append("file", file);
  return requestForm<KnowledgeDocumentDetail>(`/api/knowledge-bases/${knowledgeBaseId}/documents/file`, formData);
}

export function deleteDocument(documentId: number): Promise<void> {
  return requestJson<void>(`/api/documents/${documentId}`, {
    method: "DELETE",
  });
}
