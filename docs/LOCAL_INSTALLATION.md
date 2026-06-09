# 本地安装部署指南

本文档用于在本机安装并运行 `kk-knowledge-agent`，包含：

- 本地知识库服务安装：Backend + Frontend
- MCP Server 安装：供 Codex、Claude Code 等 Agent 调用外接知识库
- 基础验证与常见问题

当前项目暂不使用 Docker；Docker Compose 仅作为后续优化方向保留。

## 1. 环境要求

建议环境：

```text
Python: 3.11 或 3.12
Node.js: 20+
npm: 10+
Git: 任意较新版本
```

项目使用的主要组件：

```text
Backend: FastAPI + SQLite + SQLAlchemy
Vector DB: ChromaDB
Embedding: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
Frontend: React + Vite + TypeScript
MCP Server: Python MCP SDK
```

首次安装完整后端依赖时会下载 PyTorch、ChromaDB、sentence-transformers 及 embedding 模型，耗时较长是正常的。

## 2. 克隆项目

```bash
git clone https://github.com/kanna12580/kk-knowledge-agent.git
cd kk-knowledge-agent
```

如果已经在本地仓库中：

```bash
git pull
```

## 3. 本地知识库 Backend 安装

进入后端目录：

```bash
cd backend
```

创建虚拟环境：

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows CMD:

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

如果官方 PyPI 较慢，可以临时指定国内源，例如：

```bash
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

复制环境变量文件：

Windows:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

默认 `.env.example` 内容已经适合本地开发：

```text
DATABASE_URL=sqlite:///./data/kk_knowledge.db
CHROMA_PERSIST_DIR=./chroma
CHROMA_COLLECTION_NAME=kk_knowledge_chunks
EMBEDDING_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
VECTOR_INDEX_ENABLED=true
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

启动后端：

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

访问：

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/health
```

健康检查应返回：

```json
{"status":"ok"}
```

## 4. 真实后端链路验证

项目提供了一个真实联调脚本，用临时 SQLite 和 Chroma 目录验证：

- 创建知识库
- 上传《春》《故乡》片段
- 写入真实 Chroma 向量
- 使用真实 embedding 模型检索
- 验证搜索排序

在仓库根目录运行：

```bash
python backend/scripts/validate_real_backend.py
```

预期结果：

```text
春天 -> 春
花草 -> 春
少年闰土 -> 故乡
小孩子 -> 故乡
乡下少年 -> 故乡
```

第一次运行会下载 embedding 模型，可能较慢。

## 5. Frontend 安装与启动

打开新终端，进入前端目录：

```bash
cd frontend
```

安装依赖：

```bash
npm install
```

启动开发服务：

```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

访问：

```text
http://localhost:5173
```

前端 Demo 支持：

```text
1. 创建知识库
2. 删除知识库
3. 上传文本
4. 上传 txt 文件
5. 删除文档
6. 普通语义搜索
7. 流式结果展示
```

构建检查：

```bash
npm run build
```

## 6. 本地知识库演示流程

推荐按这个顺序验证：

```text
1. 启动 Backend
2. 启动 Frontend
3. 打开 http://localhost:5173
4. 创建知识库：现代文学
5. 上传文本《春》
6. 上传文本《故乡》
7. 搜索：春天
8. 搜索：少年闰土
9. 使用流式搜索：小孩子
10. 删除测试文档
11. 删除测试知识库
```

注意：

- 上传文档时会触发 embedding 和 Chroma 写入。
- 第一次向量化可能较慢。
- 删除知识库/文档时，Backend 会同步删除对应 Chroma 向量。

## 7. MCP Server 安装

MCP Server 是 Agent 适配层，只调用 Backend API，不重复实现检索逻辑。

打开新终端，进入 MCP 目录：

```bash
cd mcp-server
```

创建虚拟环境：

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

复制环境变量文件：

Windows:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

默认配置：

```text
BACKEND_API_URL=http://localhost:8000
BACKEND_TIMEOUT_SECONDS=10
```

如果 Backend 运行在 `127.0.0.1:8000`，可以将 `.env` 改为：

```text
BACKEND_API_URL=http://127.0.0.1:8000
BACKEND_TIMEOUT_SECONDS=10
```

## 8. 启动 MCP Server

确保 Backend 已启动，然后运行：

```bash
python server.py
```

MCP Server 提供工具：

```text
search_knowledge_base
list_knowledge_bases
add_text_document
```

工具职责：

```text
search_knowledge_base:
  输入 query、knowledge_base_id、top_k
  调用 Backend /api/search
  返回语义检索结果

list_knowledge_bases:
  调用 Backend /api/knowledge-bases
  返回知识库列表

add_text_document:
  调用 Backend /api/knowledge-bases/{id}/documents/text
  添加文本知识
```

## 9. MCP 客户端配置示例

不同 Agent 客户端的配置文件位置不同，但核心配置类似。

推荐使用绝对路径，避免工作目录不一致导致找不到 `server.py`。

示例：

```json
{
  "mcpServers": {
    "kk-knowledge": {
      "command": "python",
      "args": [
        "C:/Users/16327/Documents/kk knowledge agent skill/mcp-server/server.py"
      ],
      "env": {
        "BACKEND_API_URL": "http://127.0.0.1:8000",
        "BACKEND_TIMEOUT_SECONDS": "10"
      }
    }
  }
}
```

如果你的客户端支持在 MCP Server 目录中启动，也可以用相对路径：

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

## 10. MCP 调用示例

Agent 可以这样调用工具：

```text
search_knowledge_base(
  query="春天相关内容",
  knowledge_base_id=1,
  top_k=5
)
```

返回示例：

```json
{
  "query": "春天相关内容",
  "results": [
    {
      "document_id": 1,
      "title": "春",
      "chunk": "盼望着，盼望着，东风来了...",
      "score": 0.89
    }
  ]
}
```

## 11. 测试

在仓库根目录运行完整测试：

```bash
python -m pytest
```

当前覆盖：

```text
Backend 知识库 CRUD
Backend 文档上传和删除
Backend chunk 切分
Backend embedding/Chroma 编排
Backend 普通搜索和流式搜索
MCP 工具正常与错误路径
```

前端构建测试：

```bash
cd frontend
npm run build
```

## 12. 常见问题

### 12.1 访问前端时报 Failed to fetch

通常是 Backend 未启动，或 CORS origin 不在允许列表中。

检查：

```text
Backend 是否运行在 http://127.0.0.1:8000
frontend/.env 中 VITE_API_BASE_URL 是否正确
backend/.env 中 CORS_ORIGINS 是否包含前端地址
```

建议：

```text
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 12.2 第一次上传文档很慢

第一次上传会加载 sentence-transformers 模型，并写入 ChromaDB。

如果模型尚未下载，还会从 Hugging Face 下载模型文件。

### 12.3 Chroma 或模型依赖安装慢

可以尝试更换 pip 源：

```bash
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

如果遇到 SSL 或代理问题，切回官方源：

```bash
pip install -r requirements.txt -i https://pypi.org/simple
```

### 12.4 MCP Tool 返回 Backend service unavailable

检查：

```text
1. Backend 是否启动
2. MCP .env 中 BACKEND_API_URL 是否正确
3. Backend /health 是否可访问
```

### 12.5 MCP Tool 返回 Backend request timed out

可能原因：

```text
1. 首次加载 embedding 模型较慢
2. 上传或检索数据较大
3. Backend 正在执行向量写入
```

可以临时调大：

```text
BACKEND_TIMEOUT_SECONDS=30
```

## 13. 当前基础开发状态

基础 MVP 已完成：

```text
1. 知识库 CRUD 与分页
2. 文本上传
3. txt 文件上传
4. chunk 切分
5. embedding 和 ChromaDB 写入
6. 文档/知识库删除时同步删除向量
7. 普通语义搜索
8. SSE 流式搜索接口
9. React 前端 Demo
10. MCP Server 工具
11. Backend 和 MCP 测试
12. 本地真实后端验证脚本
```

后续重点优化：

```text
1. 接入 LLM 做真正 RAG 回答
2. 将当前流式搜索升级为流式回答生成
3. 增加 PDF/DOCX 上传
4. 增加 BM25 + 向量混合检索
5. 增加 rerank
6. 增加 Docker Compose 一键部署
```

## 14. Codex MCP Local Install Note

Codex MCP config path on this machine:

```text
C:\Users\16327\.codex\config.toml
```

Installed server config:

```toml
[mcp_servers.kk_knowledge]
command = 'C:\Users\16327\AppData\Local\Programs\Python\Python312\python.exe'
args = ['C:\Users\16327\Documents\kk knowledge agent skill\mcp-server\server.py']
startup_timeout_sec = 120

[mcp_servers.kk_knowledge.env]
BACKEND_API_URL = 'http://127.0.0.1:8000'
BACKEND_TIMEOUT_SECONDS = '30'
```

Validation notes:

```text
1. Backend must be running at http://127.0.0.1:8000 before Codex calls the MCP tools.
2. Codex CLI recognizes kk_knowledge via `codex mcp list`.
3. A new Codex process can see the tool and starts `kk_knowledge/list_knowledge_bases`.
4. Non-interactive `codex exec` may cancel MCP tool calls because no user approval UI is available.
5. Restart Codex Desktop or open a new session, then approve the MCP tool call to complete live querying.
6. The Python command must point to the interpreter with the `mcp` SDK installed. This machine uses Python312.
```
