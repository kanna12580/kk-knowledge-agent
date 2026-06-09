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

状态：已完成。

内容：
- 实现知识库列表和创建。
- 实现文本上传和 txt 上传。
- 实现搜索框和流式结果展示。
- 使用 `fetch + ReadableStream` 处理 POST SSE。
- 新增 React/Vite 单页 Demo：左侧知识库，中间文档上传，右侧搜索和流式结果。
- 新增前端 API client：knowledge、documents、search。
- 新增工具型响应式布局和基础状态提示。
- 安装前端依赖并提交 `package-lock.json`。
- 扩展 `backend/.env.example` 的 CORS 示例，加入 `http://127.0.0.1:5173`。

验证：
- 命令：`npm run build`
- 结果：TypeScript 和 Vite build 通过。
- 浏览器验证：`http://localhost:5173`
- 创建知识库成功。
- 上传文本《春》成功。
- 普通搜索 `春天` 成功返回《春》。
- 流式搜索 `春天` 成功展示 `delta` 和 `result` 事件。

验证中发现并修复：
- `127.0.0.1:5173` 打开前端时会触发 CORS，因为后端默认只允许 `localhost:5173`；已在 `.env.example` 中补充 127.0.0.1。
- 知识库创建后，`event.currentTarget` 在 await 后为空导致 form reset 控制台报错；已改为 await 前保存 form 引用。
- 流式按钮最初没有触发流式搜索，因为 `FormData(form)` 不能可靠读取 submit button 的 intent；已改用 `SubmitEvent.submitter`。

## 2026-06-09 - Frontend Delete Controls

状态：已完成。

内容：
- 前端新增删除知识库能力，调用 `DELETE /api/knowledge-bases/{kb_id}`。
- 前端新增删除文档能力，调用 `DELETE /api/documents/{document_id}`。
- 删除操作使用行内二次确认：第一次点击垃圾桶进入确认态，第二次点击“确认”才执行删除。
- 删除知识库后会刷新选择状态，并清空关联文档、搜索结果和流式输出。
- 删除文档后会移除文档列表项，并清理当前搜索结果中对应文档的命中。

验证：
- 命令：`npm run build`
- 结果：TypeScript 和 Vite build 通过。
- 后端 DELETE 链路验证：临时文档和临时知识库删除成功。

验证说明：
- 浏览器会话在原生 confirm 验证时触发安全拦截，后续不再继续使用该会话硬测同一地址。
- 已将前端原生 `window.confirm` 改为行内二次确认，避免浏览器弹窗阻塞演示和自动化验证。

## 2026-06-09 - Phase 6 MCP Server

状态：已完成。

内容：
- 新增 MCP Server 入口：`mcp-server/server.py`。
- 新增 MCP 工具实现：`mcp-server/tools.py`。
- 必做工具：`search_knowledge_base`。
- 加分工具：`list_knowledge_bases`、`add_text_document`。
- MCP Server 只通过 HTTP 调用 Backend API，不重复实现检索逻辑。
- Backend 地址从 `BACKEND_API_URL` 读取，默认 `http://localhost:8000`。
- Backend 超时从 `BACKEND_TIMEOUT_SECONDS` 读取，默认 10 秒。
- 错误路径返回结构化错误：空 query、404、后端不可用、超时、空结果。

验证：
- 安装 `mcp-server/requirements.txt` 成功。
- 命令：`python -m pytest`
- 结果：`37 passed, 1 warning`
- 命令：导入 `mcp-server/server.py`
- 结果：`FastMCP` 实例可正常加载。

测试覆盖：
- `search_knowledge_base` 正常返回结果。
- query 为空返回错误。
- 后端 404 返回错误。
- 后端超时返回错误。
- 空检索结果返回提示。
- `list_knowledge_bases` 正常返回列表。
- `add_text_document` 正常添加文本。

## 2026-06-09 - Base MVP Closure And Local Installation Docs

状态：已完成。

内容：
- 对照 `AGENTS.md` 和交接文档检查阶段 0-6 基础开发完成情况。
- 新增本地安装部署文档：`docs/LOCAL_INSTALLATION.md`。
- 文档覆盖 Backend、Frontend、本地真实后端验证、MCP Server 安装、MCP 客户端配置、测试和常见问题。
- README 增加本地安装部署文档入口。

验证：
- 命令：`python -m pytest`
- 结果：`37 passed, 1 warning`
- 命令：`npm run build`
- 结果：TypeScript 和 Vite build 通过。

结论：
- 基础 MVP 已完成，没有发现阻塞阶段 7 交付文档整理的开发遗漏。
- 后续主线可进入 README/API 示例/面试演示流程完善，或进入 RAG/LLM 优化方向。

## 2026-06-09 - Codex MCP Install Validation

状态：已完成安装配置，真实 Codex 调用需重启或新会话后批准工具调用。

内容：
- 将本项目 MCP Server 注册到本机 Codex 配置：`C:\Users\16327\.codex\config.toml`。
- MCP Server 名称：`kk_knowledge`。
- 启动命令指向 `mcp-server/server.py`。
- 环境变量固定为 `BACKEND_API_URL=http://127.0.0.1:8000`，避免 `localhost` 解析差异。
- 初次配置使用 Python39 时，Codex MCP 握手失败；原因是该解释器在当前环境中拒绝访问，且 MCP SDK 实际安装在 Python312。
- 已修正为：`C:\Users\16327\AppData\Local\Programs\Python\Python312\python.exe`。

验证：
- Backend 直接查询成功：
  - `GET /api/knowledge-bases` 返回验证知识库。
  - `POST /api/search` 使用 `knowledge_base_id=2` 能命中 `MCP 验证文档`。
- `codex mcp list` 已识别 `kk_knowledge`，状态为 enabled。
- 新的 `codex exec` 进程已能发现并发起 `kk_knowledge/list_knowledge_bases` MCP tool call。
- 非交互 `codex exec` 中 MCP tool call 被标记为 `user cancelled`，因此没有继续执行 `search_knowledge_base`。

结论：
- MCP Server 已安装进 Codex 配置，且真实 Codex 进程已能看到并尝试调用工具。
- 当前桌面会话不会热加载新 MCP 工具；需要重启 Codex Desktop 或新开会话。
- 在新会话首次调用时，需要批准 MCP tool call，之后即可让 Codex 查询知识库内容。

## 2026-06-09 - Codex MCP Proxy Fix

状态：已完成代码修复，需重启 Codex 以重新加载 MCP Server 进程。

问题：
- 重启 Codex 后，`mcp__kk_knowledge` 工具已在当前会话暴露。
- 真实调用 `search_knowledge_base` 时返回 `Bad Gateway`。
- 同一查询直接访问 Backend `POST /api/search` 成功，说明 Backend、数据库、Chroma 和 embedding 检索链路正常。

原因：
- MCP Server 里的 `httpx.AsyncClient` 默认会继承进程环境中的代理配置。
- Codex 启动 MCP Server 时可能带有代理相关环境，导致访问本地 `127.0.0.1:8000` 被错误转发到代理，从而返回 `Bad Gateway`。

修复：
- 在 `mcp-server/tools.py` 中创建 Backend HTTP client 时设置 `trust_env=False`。
- MCP Server 调 Backend 时不再继承外部代理环境，确保本地知识库服务直连。
- MCP 测试中补充断言，防止该配置被回退。

验证：
- `python -m pytest mcp-server/tests` -> `7 passed`
- `python -m pytest` -> `37 passed, 1 warning`
- 直接 Backend 查询 `knowledge_base_id=2` 可命中 `MCP 验证文档`。

说明：
- 当前已运行的 Codex MCP 子进程不会热加载代码变更。
- 重启 Codex Desktop 或新开可重新初始化 MCP Server 的会话后，`kk_knowledge` 会加载本次修复。

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
