import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { createKnowledgeBase, listKnowledgeBases } from "./api/knowledge";
import { listDocuments, uploadTextDocument, uploadTxtDocument } from "./api/documents";
import { searchKnowledgeBase, streamSearchKnowledgeBase } from "./api/search";
import type { KnowledgeBase, KnowledgeDocument, SearchResult, StreamEvent } from "./api/types";
import { KnowledgeBaseList } from "./components/KnowledgeBaseList";
import { DocumentUploader } from "./components/DocumentUploader";
import { SearchPanel } from "./components/SearchPanel";

type Notice = { type: "success" | "error"; message: string } | null;

export default function App() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<KnowledgeBase | null>(null);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
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

  const refreshKnowledgeBases = useCallback(async () => {
    setLoadingKnowledge(true);
    try {
      const page = await listKnowledgeBases();
      setKnowledgeBases(page.items);
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
    async (knowledgeBaseId: number) => {
      setLoadingDocuments(true);
      try {
        const page = await listDocuments(knowledgeBaseId);
        setDocuments(page.items);
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
      return;
    }
    void refreshDocuments(selectedId);
  }, [refreshDocuments, selectedId]);

  const selectedName = useMemo(() => selectedKnowledgeBase?.name ?? "未选择知识库", [selectedKnowledgeBase]);

  async function handleCreateKnowledgeBase(payload: { name: string; description: string }) {
    try {
      const created = await createKnowledgeBase(payload);
      setKnowledgeBases((current) => [created, ...current]);
      setSelectedKnowledgeBase(created);
      showNotice({ type: "success", message: "知识库已创建" });
    } catch (error) {
      showNotice({ type: "error", message: error instanceof Error ? error.message : "创建失败" });
    }
  }

  async function handleUploadText(payload: { title: string; content: string }) {
    if (!selectedKnowledgeBase) {
      return;
    }
    setLoadingDocuments(true);
    try {
      const created = await uploadTextDocument(selectedKnowledgeBase.id, payload);
      setDocuments((current) => [created, ...current]);
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
      const created = await uploadTxtDocument(selectedKnowledgeBase.id, payload.title, payload.file);
      setDocuments((current) => [created, ...current]);
      showNotice({ type: "success", message: "文件已上传" });
    } catch (error) {
      showNotice({ type: "error", message: error instanceof Error ? error.message : "上传失败" });
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
          onCreate={handleCreateKnowledgeBase}
          onRefresh={refreshKnowledgeBases}
          onSelect={setSelectedKnowledgeBase}
        />
        <DocumentUploader
          selectedKnowledgeBase={selectedKnowledgeBase}
          documents={documents}
          loading={loadingDocuments}
          onUploadText={handleUploadText}
          onUploadFile={handleUploadFile}
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

