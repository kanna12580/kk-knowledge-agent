import { ChevronLeft, ChevronRight, Database, Loader2, Plus, RefreshCw, Trash2 } from "lucide-react";
import type { FormEvent } from "react";
import { useState } from "react";
import type { KnowledgeBase } from "../api/types";

interface KnowledgeBaseListProps {
  knowledgeBases: KnowledgeBase[];
  selectedId: number | null;
  loading: boolean;
  pagination: { page: number; pageSize: number; total: number };
  onCreate: (payload: { name: string; description: string }) => Promise<void>;
  onDelete: (knowledgeBase: KnowledgeBase) => Promise<void>;
  onPageChange: (page: number) => Promise<void>;
  onRefresh: () => Promise<void>;
  onSelect: (knowledgeBase: KnowledgeBase) => void;
}

export function KnowledgeBaseList({
  knowledgeBases,
  selectedId,
  loading,
  pagination,
  onCreate,
  onDelete,
  onPageChange,
  onRefresh,
  onSelect,
}: KnowledgeBaseListProps) {
  const [pendingDeleteId, setPendingDeleteId] = useState<number | null>(null);
  const totalPages = Math.max(1, Math.ceil(pagination.total / pagination.pageSize));

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    await onCreate({
      name: String(formData.get("name") ?? ""),
      description: String(formData.get("description") ?? ""),
    });
    form.reset();
  }

  return (
    <section className="panel sidebar-panel" aria-label="知识库">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Knowledge Bases</p>
          <h2>知识库</h2>
        </div>
        <button className="icon-button" type="button" onClick={onRefresh} title="刷新" disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <RefreshCw size={18} />}
        </button>
      </div>

      <form className="create-form" onSubmit={handleSubmit}>
        <label>
          名称
          <input name="name" maxLength={120} placeholder="现代文学" required />
        </label>
        <label>
          描述
          <textarea name="description" rows={3} placeholder="朱自清和鲁迅文章" />
        </label>
        <button className="primary-button" type="submit">
          <Plus size={17} />
          创建
        </button>
      </form>

      <div className="list-block">
        {knowledgeBases.length === 0 ? (
          <div className="empty-state">暂无知识库</div>
        ) : (
          knowledgeBases.map((item) => (
            <div
              className={`kb-row ${item.id === selectedId ? "active" : ""}`}
              key={item.id}
            >
              <button
                className="row-main-button"
                type="button"
                onClick={() => {
                  setPendingDeleteId(null);
                  onSelect(item);
                }}
              >
                <Database size={18} />
                <span>
                  <strong>{item.name}</strong>
                  <small>{item.description || "无描述"}</small>
                </span>
              </button>
              <button
                className={`danger-icon-button ${pendingDeleteId === item.id ? "confirm" : ""}`}
                type="button"
                onClick={() => {
                  if (pendingDeleteId === item.id) {
                    void onDelete(item).finally(() => setPendingDeleteId(null));
                    return;
                  }
                  setPendingDeleteId(item.id);
                }}
                title={pendingDeleteId === item.id ? "确认删除知识库" : "删除知识库"}
              >
                {pendingDeleteId === item.id ? <span>确认</span> : <Trash2 size={17} />}
              </button>
            </div>
          ))
        )}
      </div>

      <div className="pagination-bar">
        <button
          className="icon-button"
          type="button"
          onClick={() => void onPageChange(pagination.page - 1)}
          title="Previous page"
          disabled={loading || pagination.page <= 1}
        >
          <ChevronLeft size={18} />
        </button>
        <span>
          Page {pagination.page} / {totalPages} · {pagination.total} total
        </span>
        <button
          className="icon-button"
          type="button"
          onClick={() => void onPageChange(pagination.page + 1)}
          title="Next page"
          disabled={loading || pagination.page >= totalPages}
        >
          <ChevronRight size={18} />
        </button>
      </div>
    </section>
  );
}
