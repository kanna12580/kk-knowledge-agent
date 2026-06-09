# Development Log

本文件记录项目开发过程中的阶段成果、关键决策、验证方式和遗留风险。后续每个阶段开发完成后都要更新，方便问题溯源。

## 2026-06-09 - Repository Initialization

状态：已完成并推送。

提交：
- `f3adeb9 Initial project scaffold`
- `bf1a1d5 Add project handoff document`

内容：
- 初始化 Git 仓库，默认分支为 `main`。
- 配置远程仓库：`https://github.com/kanna12580/kk-knowledge-agent.git`。
- 新增基础目录：`backend/`、`frontend/`、`mcp-server/`、`examples/`。
- 新增 `README.md`、`AGENTS.md`、`docs/PROJECT_HANDOFF.md`。
- 暂不引入 Docker；仅在后续优化方向保留 Docker Compose 一键部署。

验证：
- `git push -u origin main` 成功。
- GitHub 远程已有初始化内容。

## 2026-06-09 - Phase 1 Backend Base API

状态：已完成并推送。

提交：
- `df7186d Implement knowledge base CRUD API`

内容：
- 初始化 FastAPI app。
- 建立配置模块、SQLAlchemy engine/session/base。
- 定义 `knowledge_bases` 表。
- 实现知识库创建、分页查询、详情、更新、删除。
- 不存在资源返回 `404 Knowledge base not found.`。
- 新增 pytest 配置和知识库 CRUD 测试。

验证：
- 命令：`python -m pytest`
- 结果：`8 passed, 1 warning`
- warning 来源：FastAPI/Starlette TestClient 关于 `httpx` 依赖版本的提示，不影响阶段一功能。

环境说明：
- 为运行阶段一测试，已安装轻量依赖：`fastapi`、`sqlalchemy`、`pydantic-settings`、`pytest`、`httpx`。
- 暂未安装 ChromaDB、sentence-transformers 等大依赖。

## 2026-06-09 - Phase 2 Document Upload And Chunking

状态：已完成。

内容：
- 定义 `documents` 和 `document_chunks` 表。
- 实现文本上传、txt 文件上传。
- 实现文档列表、详情、删除。
- 实现基础 chunk 切分，默认 `chunk_size=500`、`chunk_overlap=80`。
- 增加上传和文档接口测试。

验证：
- 命令：`python -m pytest`
- 结果：`20 passed, 1 warning`
- warning 来源：FastAPI/Starlette TestClient 关于 `httpx` 依赖版本的提示，不影响阶段二功能。

环境说明：
- 为运行文件上传测试，已安装 `python-multipart`。

遗留到阶段三：
- 当前删除文档只删除 SQLite 中的 document/chunk 记录。
- ChromaDB 向量写入和删除同步将在阶段三接入向量库时补齐。

## 2026-06-09 - Phase 3 Embedding And ChromaDB

状态：已完成。

内容：
- 封装 sentence-transformers embedding。
- 封装 ChromaDB collection 初始化。
- 上传文档后为 chunks 生成向量并写入 ChromaDB。
- 将 Chroma vector id 回写到 `document_chunks.vector_id`。
- 删除知识库/文档时同步删除向量。
- 新增 `VECTOR_INDEX_ENABLED` 配置，真实运行默认启用，测试环境默认关闭。
- 向量写入失败时回滚文档创建，并返回明确错误。

验证：
- 命令：`python -m pytest`
- 结果：`24 passed, 1 warning`
- warning 来源：FastAPI/Starlette TestClient 关于 `httpx` 依赖版本的提示，不影响阶段三功能。

测试策略：
- 阶段三测试使用 fake embedding 和 fake Chroma client，验证业务编排、metadata、vector_id 回写和删除同步。
- 未在测试中下载真实 embedding 模型，避免阶段开发被大模型依赖拖慢。

环境说明：
- 当前本机尚未安装 `chromadb` 和 `sentence-transformers`。
- 若要真实跑向量化上传，需要先安装完整 `backend/requirements.txt`。

遗留到阶段四：
- Chroma query 检索接口尚未实现。
- 需要基于 query embedding 和 `knowledge_base_id` metadata 过滤实现语义搜索。

## 2026-06-09 - Phase 4 Semantic Search And Streaming

状态：已完成。

内容：
- 实现 `POST /api/search`。
- query embedding 后按 `knowledge_base_id` 过滤 Chroma。
- 返回 `document_id`、`title`、`chunk`、`score`。
- 实现 `POST /api/search/stream` SSE 流式接口。
- 新增检索结果 schema 和 Chroma query 封装。
- 普通搜索失败返回明确 `500 Failed to search knowledge base.`。
- 流式搜索按 `start`、`delta`、`result`、`error`、`done` 事件输出。

验证：
- 命令：`python -m pytest`
- 结果：`30 passed, 1 warning`
- warning 来源：FastAPI/Starlette TestClient 关于 `httpx` 依赖版本的提示，不影响阶段四功能。

测试策略：
- 阶段四测试继续使用 fake embedding 和 fake Chroma query 结果。
- 覆盖普通搜索成功、空 query、知识库不存在、检索失败、流式成功和流式错误事件。

遗留到真实联调：
- 需要安装完整 `backend/requirements.txt` 后，用真实 ChromaDB 和 embedding 模型验证《春》《故乡》的检索效果。

## 2026-06-09 - Phase 5 Frontend Demo

状态：未开始。

计划：
- 实现知识库列表和创建。
- 实现文本上传和 txt 上传。
- 实现搜索框和流式结果展示。
- 使用 `fetch + ReadableStream` 处理 POST SSE。

## 2026-06-09 - Pre-Phase 5 Real Backend Validation

状态：已完成。

内容：
- 安装完整 `backend/requirements.txt`。
- 下载并加载真实 embedding 模型：`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`。
- 新增真实后端联调脚本：`backend/scripts/validate_real_backend.py`。
- 脚本使用临时 SQLite 和临时 Chroma 目录，不污染本地正式数据。
- 通过 FastAPI endpoints 创建知识库、上传《春》《故乡》片段，并执行真实语义搜索。
- 将 `posthog` pin 到 `<6.0`，避免 `chromadb 0.6.x` 与新版 `posthog 7.x` 的 telemetry 兼容报错。
- 将搜索分数从 `1 - distance` 调整为 `1 / (1 + distance)`，避免真实 Chroma distance 大于 1 时分数被压成 0。

验证：
- 命令：`python -m pytest`
- 结果：`30 passed, 1 warning`
- 命令：`python backend/scripts/validate_real_backend.py`
- 结果：真实 Chroma 写入和搜索成功，脚本退出码为 0。

真实搜索结果：
- `春天` -> top result `春`
- `花草` -> top result `春`
- `少年闰土` -> top result `故乡`
- `小孩子` -> top result `故乡`
- `乡下少年` -> top result `故乡`

遗留说明：
- 当前唯一 warning 来源仍是 FastAPI/Starlette TestClient 关于 `httpx` 的提示，不影响真实后端能力。
- 前端阶段可以基于当前后端 API 继续开发。
