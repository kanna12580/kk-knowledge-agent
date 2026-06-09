import { FileText, Loader2, Send, Upload } from "lucide-react";
import type { ChangeEvent, FormEvent } from "react";
import type { KnowledgeBase, KnowledgeDocument } from "../api/types";

interface DocumentUploaderProps {
  selectedKnowledgeBase: KnowledgeBase | null;
  documents: KnowledgeDocument[];
  loading: boolean;
  onUploadText: (payload: { title: string; content: string }) => Promise<void>;
  onUploadFile: (payload: { title: string; file: File }) => Promise<void>;
}

export function DocumentUploader({
  selectedKnowledgeBase,
  documents,
  loading,
  onUploadText,
  onUploadFile,
}: DocumentUploaderProps) {
  async function handleTextSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    await onUploadText({
      title: String(formData.get("title") ?? ""),
      content: String(formData.get("content") ?? ""),
    });
    form.reset();
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.currentTarget.files?.[0];
    if (!file) {
      return;
    }

    const title = file.name.replace(/\.txt$/i, "");
    await onUploadFile({ title, file });
    event.currentTarget.value = "";
  }

  const disabled = !selectedKnowledgeBase || loading;

  return (
    <section className="panel document-panel" aria-label="文档">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Documents</p>
          <h2>{selectedKnowledgeBase ? selectedKnowledgeBase.name : "未选择"}</h2>
        </div>
        {loading ? <Loader2 className="spin muted-icon" size={20} /> : <FileText className="muted-icon" size={20} />}
      </div>

      <form className="document-form" onSubmit={handleTextSubmit}>
        <label>
          标题
          <input name="title" placeholder="春" required disabled={disabled} />
        </label>
        <label>
          文本
          <textarea name="content" rows={9} placeholder="盼望着，盼望着，东风来了..." required disabled={disabled} />
        </label>
        <div className="toolbar-row">
          <button className="primary-button" type="submit" disabled={disabled}>
            <Send size={17} />
            上传文本
          </button>
          <label className={`file-button ${disabled ? "disabled" : ""}`}>
            <Upload size={17} />
            txt
            <input type="file" accept=".txt,text/plain" onChange={handleFileChange} disabled={disabled} />
          </label>
        </div>
      </form>

      <div className="document-list">
        {documents.length === 0 ? (
          <div className="empty-state">暂无文档</div>
        ) : (
          documents.map((document) => (
            <article className="document-row" key={document.id}>
              <div>
                <strong>{document.title}</strong>
                <small>{document.source_type === "file" ? document.file_name : "text"}</small>
              </div>
              <span>{new Date(document.created_at).toLocaleDateString()}</span>
            </article>
          ))
        )}
      </div>
    </section>
  );
}

