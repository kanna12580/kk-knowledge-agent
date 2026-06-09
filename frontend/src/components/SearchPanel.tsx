import { Loader2, Search, Send } from "lucide-react";
import type { FormEvent } from "react";
import type { KnowledgeBase, SearchResult } from "../api/types";
import { StreamingResult } from "./StreamingResult";

interface SearchPanelProps {
  selectedKnowledgeBase: KnowledgeBase | null;
  results: SearchResult[];
  streamLines: string[];
  loading: boolean;
  streaming: boolean;
  onSearch: (payload: { query: string; topK: number }) => Promise<void>;
  onStreamSearch: (payload: { query: string; topK: number }) => Promise<void>;
}

export function SearchPanel({
  selectedKnowledgeBase,
  results,
  streamLines,
  loading,
  streaming,
  onSearch,
  onStreamSearch,
}: SearchPanelProps) {
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const submitter = (event.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null;
    const payload = {
      query: String(formData.get("query") ?? ""),
      topK: Number(formData.get("topK") ?? 5),
    };
    const intent = submitter?.value ?? "search";
    if (intent === "stream") {
      await onStreamSearch(payload);
      return;
    }
    await onSearch(payload);
  }

  const disabled = !selectedKnowledgeBase || loading || streaming;

  return (
    <section className="panel search-panel" aria-label="搜索">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Retrieval</p>
          <h2>搜索</h2>
        </div>
        {loading || streaming ? <Loader2 className="spin muted-icon" size={20} /> : <Search className="muted-icon" size={20} />}
      </div>

      <form className="search-form" onSubmit={handleSubmit}>
        <label>
          Query
          <textarea name="query" rows={4} placeholder="少年闰土" required disabled={disabled} />
        </label>
        <label>
          Top K
          <input name="topK" type="number" min={1} max={20} defaultValue={5} disabled={disabled} />
        </label>
        <div className="toolbar-row">
          <button className="primary-button" type="submit" name="intent" value="search" disabled={disabled}>
            <Search size={17} />
            搜索
          </button>
          <button className="secondary-button" type="submit" name="intent" value="stream" disabled={disabled}>
            <Send size={17} />
            流式
          </button>
        </div>
      </form>

      <div className="result-list">
        {results.length === 0 ? (
          <div className="empty-state">暂无结果</div>
        ) : (
          results.map((result, index) => (
            <article className="result-row" key={`${result.document_id}-${result.chunk_id ?? index}`}>
              <div className="result-meta">
                <strong>{result.title || `文档 ${result.document_id}`}</strong>
                <span>{result.score.toFixed(4)}</span>
              </div>
              <p>{result.chunk}</p>
            </article>
          ))
        )}
      </div>

      <StreamingResult lines={streamLines} />
    </section>
  );
}
