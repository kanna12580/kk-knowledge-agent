import { Database, Loader2, Plus, RefreshCw } from "lucide-react";
import type { FormEvent } from "react";
import type { KnowledgeBase } from "../api/types";

interface KnowledgeBaseListProps {
  knowledgeBases: KnowledgeBase[];
  selectedId: number | null;
  loading: boolean;
  onCreate: (payload: { name: string; description: string }) => Promise<void>;
  onRefresh: () => Promise<void>;
  onSelect: (knowledgeBase: KnowledgeBase) => void;
}

export function KnowledgeBaseList({
  knowledgeBases,
  selectedId,
  loading,
  onCreate,
  onRefresh,
  onSelect,
}: KnowledgeBaseListProps) {
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
            <button
              className={`kb-row ${item.id === selectedId ? "active" : ""}`}
              key={item.id}
              type="button"
              onClick={() => onSelect(item)}
            >
              <Database size={18} />
              <span>
                <strong>{item.name}</strong>
                <small>{item.description || "无描述"}</small>
              </span>
            </button>
          ))
        )}
      </div>
    </section>
  );
}
