# AGENTS.md

本文件是 `kk-knowledge-agent` 的开发导航，供 Codex/Agent 在后续任务中优先读取。项目目标是构建轻量级知识库系统：Backend 负责知识库、文档、分块、向量化与检索；Frontend 提供演示页面；MCP Server 将检索能力封装为 Agent 工具。

如果本文件的阶段计划不足以判断产品边界、接口细节、演示路径或验收口径，优先参考 `docs/PROJECT_HANDOFF.md`。

项目后续演进有两条主线：
- RAG 应用：Backend 检索 chunks 后接入 LLM，生成带引用依据的回答；此时流式接口主要用于逐步返回 LLM 生成内容。
- MCP 外接知识库：MCP Server 将 Backend 检索能力暴露为 Agent 工具，Codex/Claude Code/OpenClaw 等 Agent 可调用外部知识库补充上下文。

## 全局原则

- Backend 是唯一业务核心，Frontend 和 MCP Server 不重复实现检索逻辑。
- SQLite 保存业务数据，ChromaDB 保存 chunk embedding。
- 删除知识库或文档时，必须同步删除对应 Chroma 向量。
- 同一个 Backend 检索核心要同时服务普通用户路径和 Agent 工具路径。
- 优先交付可演示 MVP，再补测试和部署优化项。
- 中文语义检索默认使用 `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`。
- API 错误必须清晰：空 query、知识库不存在、空文档、非 txt、文件过大、embedding/向量库/检索失败。

## 阶段 0：仓库与环境

目标：让项目结构稳定，后续任务能直接进入开发。

交付：
- `backend/`、`frontend/`、`mcp-server/`、`examples/` 基础目录。
- `.gitignore`、`README.md`。
- Backend 和 MCP 的 `.env.example`。
- Frontend 的 Vite/React/TypeScript 配置文件。

验收：
- `git status` 能清楚展示初始化文件。
- README 包含本地启动方式和模块说明。

## 阶段 1：Backend 基础 API

目标：完成 FastAPI 服务、SQLite 模型和知识库 CRUD。

建议文件：
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/db/database.py`
- `backend/app/db/models.py`
- `backend/app/db/schemas.py`
- `backend/app/api/knowledge_routes.py`
- `backend/app/services/knowledge_service.py`

任务：
1. 初始化 FastAPI app，挂载 `/api` 路由。
2. 建立 SQLAlchemy engine/session/base。
3. 定义 `knowledge_bases` 表。
4. 实现创建、分页查询、详情、更新、删除。
5. 为不存在资源返回 404。

验收：
- `POST /api/knowledge-bases` 可创建知识库。
- `GET /api/knowledge-bases?page=1&page_size=10` 可分页。
- CRUD 单元测试通过。

## 阶段 2：文档上传与分块

目标：支持文本输入和 txt 上传，并保存 chunks。

建议文件：
- `backend/app/api/document_routes.py`
- `backend/app/services/document_service.py`
- `backend/app/services/chunk_service.py`

任务：
1. 定义 `documents`、`document_chunks` 表。
2. 实现文本上传接口：`POST /api/knowledge-bases/{kb_id}/documents/text`。
3. 实现 txt 上传接口：`POST /api/knowledge-bases/{kb_id}/documents/file`。
4. 实现文档列表、详情、删除。
5. 分块策略：`chunk_size=500`，`chunk_overlap=80`；优先按段落，段落过长再固定长度切分。

验收：
- 空文本失败。
- 非 txt 文件失败。
- 不存在知识库失败。
- 上传后能看到 chunk 记录。

## 阶段 3：Embedding 与 ChromaDB

目标：上传文档后自动向量化并写入 ChromaDB。

建议文件：
- `backend/app/services/embedding_service.py`
- `backend/app/vector/chroma_client.py`

任务：
1. 封装 sentence-transformers embedding。
2. 封装 ChromaDB collection 初始化。
3. 上传文档后为 chunks 生成向量。
4. 写入 ChromaDB，metadata 至少包含 `knowledge_base_id`、`document_id`、`title`、`chunk_id`。
5. 将 Chroma vector id 回写到 `document_chunks.vector_id`。
6. 删除知识库/文档时同步删除向量。

验收：
- 上传《春》《故乡》后 Chroma 中有对应向量。
- 删除文档后对应向量不可再被检索。

## 阶段 4：语义检索与流式接口

目标：完成普通搜索和 SSE 流式搜索。

建议文件：
- `backend/app/api/search_routes.py`
- `backend/app/services/retrieval_service.py`
- `backend/app/services/stream_service.py`

任务：
1. 实现 `POST /api/search`。
2. 校验 query 非空、知识库存在、top_k 合理。
3. query embedding 后按 `knowledge_base_id` 过滤 Chroma。
4. 返回 document_id、title、chunk、score。
5. 实现 `POST /api/search/stream`，返回 `text/event-stream`。
6. 流式事件类型：`start`、`delta`、`result`、`error`、`done`。

验收：
- 搜索“春天”返回《春》。
- 搜索“少年闰土”返回《故乡》。
- 搜索“小孩子”返回《故乡》。
- 流式接口能逐步返回事件。

## 阶段 5：Frontend Demo

目标：用单页完成面试演示路径。

布局：
- 左侧：知识库列表与创建。
- 中间：文本输入和 txt 上传。
- 右侧：搜索框与流式结果。

建议文件：
- `frontend/src/api/client.ts`
- `frontend/src/api/knowledge.ts`
- `frontend/src/api/documents.ts`
- `frontend/src/api/search.ts`
- `frontend/src/components/KnowledgeBaseList.tsx`
- `frontend/src/components/DocumentUploader.tsx`
- `frontend/src/components/SearchPanel.tsx`
- `frontend/src/components/StreamingResult.tsx`
- `frontend/src/App.tsx`

任务：
1. 创建和选择知识库。
2. 上传文本和 txt 文件。
3. 普通搜索和流式搜索。
4. 使用 `fetch + ReadableStream` 处理 POST SSE。

验收：
- 浏览器中可完成创建知识库、上传《春》《故乡》、搜索和流式展示。

## 阶段 6：MCP Server

目标：让 Agent 能通过 MCP Tool 查询知识库。

建议文件：
- `mcp-server/server.py`
- `mcp-server/tools.py`

必做工具：
- `search_knowledge_base(query: str, knowledge_base_id: int, top_k: int = 5)`

加分工具：
- `list_knowledge_bases`
- `add_text_document`

任务：
1. MCP Server 只调用 Backend HTTP API。
2. 默认 Backend 地址从 `BACKEND_API_URL` 读取。
3. HTTP timeout 设置为 10 秒。
4. 处理后端不可用、404、超时、空结果。

验收：
- Agent 可配置并调用 `search_knowledge_base`。
- Backend 未启动时返回明确错误。

## 阶段 7：测试与交付

目标：项目可验证、可演示、可讲解。

Backend 测试：
- `test_knowledge.py`
- `test_upload.py`
- `test_search.py`

MCP 测试：
- `test_mcp_tool.py`

文档：
- README 增加启动方式、API 示例、MCP 配置、面试演示流程、后续优化方向。
- 后续优化必须保留两条方向：接入 LLM 做 RAG 流式回答；封装 MCP Server 做 Agent 外接知识库。

MVP 验收标准：
- 可以创建、查询、更新、删除知识库。
- 知识库列表支持分页。
- 可以直接输入文本和上传 txt 文件。
- 上传后自动分块和向量化。
- 可以语义搜索并流式返回结果。
- MCP Server 提供 `search_knowledge_base`。
- 常见错误均有明确响应。
