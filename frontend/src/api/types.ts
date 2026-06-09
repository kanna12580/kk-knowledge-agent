export interface KnowledgeBase {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface DocumentChunk {
  id: number;
  document_id: number;
  knowledge_base_id: number;
  chunk_index: number;
  content: string;
  vector_id: string | null;
  created_at: string;
}

export interface KnowledgeDocument {
  id: number;
  knowledge_base_id: number;
  title: string;
  source_type: "text" | "file";
  file_name: string | null;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeDocumentDetail extends KnowledgeDocument {
  chunks: DocumentChunk[];
}

export interface SearchResult {
  document_id: number;
  title: string;
  chunk: string;
  score: number;
  chunk_id: number | null;
  chunk_index: number | null;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
}

export type StreamEvent =
  | { type: "start" }
  | { type: "delta"; content: string }
  | ({ type: "result" } & SearchResult)
  | { type: "error"; message: string }
  | { type: "done" };

