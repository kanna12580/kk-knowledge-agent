# kk-knowledge-agent

轻量级知识库 Agent 项目，支持知识库管理、文本/txt 上传、分块向量化、语义检索、流式返回，并通过 MCP Server 暴露给 Agent 调用。

## Architecture

```text
Frontend
   |
   | HTTP
   v
Backend API
   |
   +--> SQLite
   +--> ChromaDB
   +--> sentence-transformers

Agent / Claude Code / OpenClaw / Hermas Agent
   |
   | MCP Tool Call
   v
MCP Server
   |
   | HTTP
   v
Backend API
```

## Repository Layout

```text
backend/       FastAPI API service
frontend/      React + Vite demo app
mcp-server/    MCP adapter server
examples/      Demo txt documents
AGENTS.md      Phased development guide for Codex/Agent
```

## Local Setup

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs:

```text
http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Demo app:

```text
http://localhost:5173
```

### MCP Server

```bash
cd mcp-server
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python server.py
```

MCP config example:

```json
{
  "mcpServers": {
    "kk-knowledge": {
      "command": "python",
      "args": ["mcp-server/server.py"]
    }
  }
}
```

## MVP Scope

- Knowledge base CRUD with pagination.
- Direct text document upload.
- `.txt` file upload.
- Chunking and local multilingual embedding.
- ChromaDB semantic retrieval.
- SSE streaming search.
- MCP tool: `search_knowledge_base`.
- Basic tests with pytest.

## Development Order

Follow [AGENTS.md](AGENTS.md) for the phased implementation plan.

## Local Installation

See [docs/LOCAL_INSTALLATION.md](docs/LOCAL_INSTALLATION.md) for detailed Backend, Frontend, and MCP Server setup.

## Future Improvements

- Add Docker Compose for one-command local deployment.
- Replace SQLite with PostgreSQL for production usage.
- Replace ChromaDB with Qdrant or Milvus for larger vector workloads.
- Add PDF/DOCX upload.
- Add BM25 + vector hybrid retrieval and rerank support.
- Add answer generation with citation highlights.
