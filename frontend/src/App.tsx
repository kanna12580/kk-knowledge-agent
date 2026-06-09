import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { createKnowledgeBase, deleteKnowledgeBase, listKnowledgeBases } from "./api/knowledge";
import { deleteDocument, listDocuments, uploadTextDocument, uploadTxtDocument } from "./api/documents";
import { searchKnowledgeBase, streamSearchKnowledgeBase } from "./api/search";
import type { KnowledgeBase, KnowledgeDocument, SearchResult, StreamEvent } from "./api/types";
import { KnowledgeBaseList } from "./components/KnowledgeBaseList";
import { DocumentUploader } from "./components/DocumentUploader";
import { SearchPanel } from "./components/SearchPanel";

type Notice = { type: "success" | "error"; message: string } | null;
type Pagination = { page: number; pageSize: number; total: number };

const KNOWLEDGE_PAGE_SIZE = 10;
const DOCUMENT_PAGE_SIZE = 10;

export default function App() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<KnowledgeBase | null>(null);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [knowledgePagination, setKnowledgePagination] = useState<Pagination>({
    page: 1,
    pageSize: KNOWLEDGE_PAGE_SIZE,
    total: 0,
  });
  const [documentPagination, setDocumentPagination] = useState<Pagination>({
    page: 1,
    pageSize: DOCUMENT_PAGE_SIZE,
    total: 0,
  });
  const [results, setResults] = useState<SearchResult[]>([]);
  const [streamLines, setStreamLines] = useState<string[]>([]);
  const [notice, setNotice] = useState<Notice>(null);
  const [loadingKnowledge, setLoadingKnowledge] = useState(false);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [searching, setSearching] = useState(false);
  const [streaming, setStreaming] = useState(false);

  const selectedId = selectedKnowledgeBase?.id ?? null;

  const showNotice = useCallback((nextNotice: Notice) => {
    setNotice(nextNotice);
    if (nextNotice) {
      window.setTimeout(() => setNotice(null), 4200);
    }
  }, []);

  const refreshKnowledgeBases = useCallback(async (pageNumber = 1) => {
    setLoadingKnowledge(true);
    try {
      const page = await listKnowledgeBases(pageNumber, KNOWLEDGE_PAGE_SIZE);
      setKnowledgeBases(page.items);
      setKnowledgePagination({ page: page.page, pageSize: page.page_size, total: page.total });
      setSelectedKnowledgeBase((current) => {
        if (current && page.items.some((item) => item.id === current.id)) {
          return current;
        }
        return page.items[0] ?? null;
      });
    } catch (error) {
      showNotice({ type: "error", message: error instanceof Error ? error.message : "知识库加载失败" });
    } finally {
      setLoadingKnowledge(false);
    }
  }, [showNotice]);

  const refreshDocuments = useCallback(
    async (knowledgeBaseId: number, pageNumber = 1) => {
      setLoadingDocuments(true);
      try {
        const page = await listDocuments(knowledgeBaseId, pageNumber, DOCUMENT_PAGE_SIZE);
        setDocuments(page.items);
        setDocumentPagination({ page: page.page, pageSize: page.page_size, total: page.total });
      } catch (error) {
        showNotice({ type: "error", message: error instanceof Error ? error.message : "文档加载失败" });
      } finally {
        setLoadingDocuments(false);
      }
    },
    [showNotice],
  );

  useEffect(() => {
    void refreshKnowledgeBases();
  }, [refreshKnowledgeBases]);

  useEffect(() => {
    if (!selectedId) {
      setDocuments([]);
      setDocumentPagination({ page: 1, pageSize: DOCUMENT_PAGE_SIZE, total: 0 });
      return;
    }
    setDocumentPagination((current) => ({ ...current, page: 1 }));
    void refreshDocuments(selectedId, 1);
  }, [refreshDocuments, selectedId]);

  const selectedName = useMemo(() => selectedKnowledgeBase?.name ?? "未选择知识库", [selectedKnowledgeBase]);

  async function handleCreateKnowledgeBase(payload: { name: string; description: string }) {
    try {
      const created = await createKnowledgeBase(payload);
      setKnowledgePagination((current) => ({ ...current, page: 1 }));
      await refreshKnowledgeBases(1);
      setSelectedKnowledgeBase(created);
      showNotice({ type: "success", message: "知识库已创建" });
    } catch (error) {
      showNotice({ type: "error", message: error instanceof Error ? error.message : "创建失败" });
    }
  }

  async function handleDeleteKnowledgeBase(knowledgeBase: KnowledgeBase) {
    setLoadingKnowledge(true);
    try {
      await deleteKnowledgeBase(knowledgeBase.id);
      const nextPage =
        knowledgeBases.length === 1 && knowledgePagination.page > 1
          ? knowledgePagination.page - 1
          : knowledgePagination.page;
      if (selectedKnowledgeBase?.id === knowledgeBase.id) {
        setDocuments([]);
        setResults([]);
        setStreamLines([]);
      }
      await refreshKnowledgeBases(nextPage);
      showNotice({ type: "success", message: "知识库已删除" });
    } catch (error) {
      showNotice({ type: "error", message: error instanceof Error ? error.message : "删除失败" });
    } finally {
      setLoadingKnowledge(false);
    }
  }

  async function handleUploadText(payload: { title: string; content: string }) {
    if (!selectedKnowledgeBase) {
      return;
    }
    setLoadingDocuments(true);
    try {
      await uploadTextDocument(selectedKnowledgeBase.id, payload);
      setDocumentPagination((current) => ({ ...current, page: 1 }));
      await refreshDocuments(selectedKnowledgeBase.id, 1);
      showNotice({ type: "success", message: "文本已上传" });
    } catch (error) {
      showNotice({ type: "error", message: error instanceof Error ? error.message : "上传失败" });
    } finally {
      setLoadingDocuments(false);
    }
  }

  async function handleUploadFile(payload: { title: string; file: File }) {
    if (!selectedKnowledgeBase) {
      return;
    }
    setLoadingDocuments(true);
    try {
      await uploadTxtDocument(selectedKnowledgeBase.id, payload.title, payload.file);
      setDocumentPagination((current) => ({ ...current, page: 1 }));
      await refreshDocuments(selectedKnowledgeBase.id, 1);
      showNotice({ type: "success", message: "文件已上传" });
    } catch (error) {
      showNotice({ type: "error", message: error instanceof Error ? error.message : "上传失败" });
    } finally {
      setLoadingDocuments(false);
    }
  }

  async function handleDeleteDocument(document: KnowledgeDocument) {
    setLoadingDocuments(true);
    try {
      await deleteDocument(document.id);
      const nextPage =
        documents.length === 1 && documentPagination.page > 1
          ? documentPagination.page - 1
          : documentPagination.page;
      if (selectedKnowledgeBase) {
        await refreshDocuments(selectedKnowledgeBase.id, nextPage);
      } else {
        setDocuments((current) => current.filter((item) => item.id !== document.id));
      }
      setResults((current) => current.filter((result) => result.document_id !== document.id));
      showNotice({ type: "success", message: "文档已删除" });
    } catch (error) {
      showNotice({ type: "error", message: error instanceof Error ? error.message : "删除失败" });
    } finally {
      setLoadingDocuments(false);
    }
  }

  async function handleSearch(payload: { query: string; topK: number }) {
    if (!selectedKnowledgeBase) {
      return;
    }
    setSearching(true);
    setStreamLines([]);
    try {
      const response = await searchKnowledgeBase({
        knowledge_base_id: selectedKnowledgeBase.id,
        query: payload.query,
        top_k: payload.topK,
      });
      setResults(response.results);
      showNotice({ type: "success", message: "搜索完成" });
    } catch (error) {
      showNotice({ type: "error", message: error instanceof Error ? error.message : "搜索失败" });
    } finally {
      setSearching(false);
    }
  }

  async function handleStreamSearch(payload: { query: string; topK: number }) {
    if (!selectedKnowledgeBase) {
      return;
    }
    setStreaming(true);
    setResults([]);
    setStreamLines([]);
    try {
      await streamSearchKnowledgeBase(
        {
          knowledge_base_id: selectedKnowledgeBase.id,
          query: payload.query,
          top_k: payload.topK,
        },
        (event: StreamEvent) => {
          if (event.type === "delta") {
            setStreamLines((current) => [...current, event.content]);
          }
          if (event.type === "result") {
            setResults((current) => [...current, event]);
            setStreamLines((current) => [...current, `${event.title} · ${event.score.toFixed(4)}`]);
          }
          if (event.type === "error") {
            setStreamLines((current) => [...current, event.message]);
          }
        },
      );
      showNotice({ type: "success", message: "流式搜索完成" });
    } catch (error) {
      showNotice({ type: "error", message: error instanceof Error ? error.message : "流式搜索失败" });
    } finally {
      setStreaming(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="top-bar">
        <div>
          <p className="eyebrow">kk-knowledge-agent</p>
          <h1>{selectedName}</h1>
        </div>
        {notice ? (
          <div className={`notice ${notice.type}`}>
            {notice.type === "success" ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
            <span>{notice.message}</span>
          </div>
        ) : null}
      </header>

      <div className="workspace-grid">
        <KnowledgeBaseList
          knowledgeBases={knowledgeBases}
          selectedId={selectedId}
          loading={loadingKnowledge}
          pagination={knowledgePagination}
          onCreate={handleCreateKnowledgeBase}
          onDelete={handleDeleteKnowledgeBase}
          onPageChange={refreshKnowledgeBases}
          onRefresh={() => refreshKnowledgeBases(knowledgePagination.page)}
          onSelect={setSelectedKnowledgeBase}
        />
        <DocumentUploader
          selectedKnowledgeBase={selectedKnowledgeBase}
          documents={documents}
          loading={loadingDocuments}
          pagination={documentPagination}
          onUploadText={handleUploadText}
          onUploadFile={handleUploadFile}
          onDeleteDocument={handleDeleteDocument}
          onPageChange={(page) => {
            if (!selectedKnowledgeBase) {
              return Promise.resolve();
            }
            return refreshDocuments(selectedKnowledgeBase.id, page);
          }}
        />
        <SearchPanel
          selectedKnowledgeBase={selectedKnowledgeBase}
          results={results}
          streamLines={streamLines}
          loading={searching}
          streaming={streaming}
          onSearch={handleSearch}
          onStreamSearch={handleStreamSearch}
        />
      </div>
    </main>
  );
}
