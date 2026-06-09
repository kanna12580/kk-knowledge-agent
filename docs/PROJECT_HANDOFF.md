# 知识库 Agent 项目开发交接文档

> 说明：本文件保存完整项目交接稿，作为 `AGENTS.md` 之外的长期参考。当前 MVP 初始化阶段暂不包含 Docker 文件；Docker Compose 保留为后续优化方向。

## 1. 项目概述

项目名称建议：

```text
kk-knowledge-agent
```

项目目标：

构建一个轻量级知识库系统，支持知识库管理、文本/txt 上传、语义检索、流式返回，并将检索能力封装为 MCP Server，供 Agent 调用。

核心能力：

```text
1. 知识库 CRUD，支持分页
2. 支持直接输入文本
3. 支持上传 txt 文件
4. 支持文本分块与向量化
5. 支持语义搜索
6. 支持流式返回搜索结果
7. 支持 MCP Tool 调用知识库查询
8. 支持基本错误处理
9. 提供前端 Demo 页面
```

推荐技术栈：

```text
Backend: FastAPI + SQLite + SQLAlchemy
Vector DB: ChromaDB
Embedding: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
Frontend: React + Vite + TypeScript
MCP Server: Python MCP SDK
Streaming: SSE / fetch ReadableStream
Testing: pytest
```

---

## 2. 整体架构

```text
kk-knowledge-agent/
  backend/       # 后端 API 服务
  frontend/      # 前端演示页面
  mcp-server/    # Agent 可调用的 MCP Server
  examples/      # 示例文章
  README.md
```

系统关系：

```text
Frontend
   |
   | HTTP
   v
Backend API
   |
   +--> SQLite
   +--> ChromaDB
   +--> Embedding Model

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

设计原则：

```text
1. Backend 是唯一业务核心。
2. Frontend 只做演示和用户操作。
3. MCP Server 只做 Agent 适配，不重复实现检索逻辑。
4. 数据库保存业务数据，向量库保存 chunk embedding。
5. 删除知识库/文档时，需要同步删除对应向量数据。
```

---

## 3. 后端模块

### 3.1 后端目录

```text
backend/
  app/
    main.py
    config.py

    api/
      knowledge_routes.py
      document_routes.py
      search_routes.py

    db/
      database.py
      models.py
      schemas.py

    services/
      knowledge_service.py
      document_service.py
      chunk_service.py
      embedding_service.py
      retrieval_service.py
      stream_service.py

    vector/
      chroma_client.py

  requirements.txt
  .env.example
```

### 3.2 数据库表设计

知识库表：

```text
knowledge_bases
- id
- name
- description
- created_at
- updated_at
```

文档表：

```text
documents
- id
- knowledge_base_id
- title
- source_type       # text / file
- file_name
- content
- created_at
- updated_at
```

分块表：

```text
document_chunks
- id
- document_id
- knowledge_base_id
- chunk_index
- content
- vector_id
- created_at
```

---

## 4. 后端 API 设计

### 4.1 知识库 CRUD

创建知识库：

```http
POST /api/knowledge-bases
```

请求：

```json
{
  "name": "现代文学",
  "description": "朱自清和鲁迅文章"
}
```

分页查询知识库：

```http
GET /api/knowledge-bases?page=1&page_size=10
```

查询详情：

```http
GET /api/knowledge-bases/{kb_id}
```

更新知识库：

```http
PUT /api/knowledge-bases/{kb_id}
```

删除知识库：

```http
DELETE /api/knowledge-bases/{kb_id}
```

删除时需要：

```text
1. 删除 knowledge_bases 记录
2. 删除 documents 记录
3. 删除 document_chunks 记录
4. 删除 ChromaDB 中对应 knowledge_base_id 的向量
```

---

### 4.2 文档上传

直接输入文本：

```http
POST /api/knowledge-bases/{kb_id}/documents/text
```

请求：

```json
{
  "title": "春",
  "content": "盼望着，盼望着，东风来了，春天的脚步近了..."
}
```

上传 txt 文件：

```http
POST /api/knowledge-bases/{kb_id}/documents/file
Content-Type: multipart/form-data
```

字段：

```text
file: chun.txt
title: 春
```

查询文档列表：

```http
GET /api/knowledge-bases/{kb_id}/documents?page=1&page_size=10
```

查询文档详情：

```http
GET /api/documents/{document_id}
```

删除文档：

```http
DELETE /api/documents/{document_id}
```

上传后处理流程：

```text
1. 校验知识库是否存在
2. 校验文本或文件内容
3. 保存 document 记录
4. 文本切分为 chunks
5. 调用 embedding 模型生成向量
6. 写入 ChromaDB
7. 保存 document_chunks 记录
```

---

### 4.3 语义搜索

普通搜索：

```http
POST /api/search
```

请求：

```json
{
  "knowledge_base_id": 1,
  "query": "少年闰土",
  "top_k": 5
}
```

响应：

```json
{
  "query": "少年闰土",
  "results": [
    {
      "document_id": 2,
      "title": "故乡",
      "chunk": "深蓝的天空中挂着一轮金黄的圆月...",
      "score": 0.86
    }
  ]
}
```

搜索流程：

```text
1. 校验 query 非空
2. 校验 knowledge_base_id 是否存在
3. 生成 query embedding
4. 在 ChromaDB 中按 knowledge_base_id 过滤查询
5. 返回 top_k 结果
```

---

### 4.4 流式搜索

流式接口：

```http
POST /api/search/stream
```

请求：

```json
{
  "knowledge_base_id": 1,
  "query": "帮我查一下春天相关内容",
  "top_k": 3
}
```

响应类型：

```http
Content-Type: text/event-stream
```

流式事件：

```text
start
delta
result
error
done
```

示例：

```text
data: {"type":"start"}

data: {"type":"delta","content":"找到"}
data: {"type":"delta","content":"与春天相关的内容："}

data: {"type":"result","document_id":1,"title":"春","score":0.89}

data: {"type":"done"}
```

---

## 5. 文本切分与向量化

### 5.1 Chunk 策略

推荐参数：

```text
chunk_size = 500
chunk_overlap = 80
```

切分逻辑：

```text
1. 优先按段落切分
2. 段落过长时按固定长度切分
3. 相邻 chunk 保留 overlap
4. 过滤空白 chunk
```

### 5.2 Embedding 模型

推荐模型：

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

理由：

```text
1. 支持中文
2. 本地可运行
3. 适合面试 Demo
4. 无需依赖外部 API
```

### 5.3 检索效果验证

示例数据：

```text
examples/chun.txt       # 朱自清《春》
examples/guxiang.txt    # 鲁迅《故乡》
```

测试 Query：

```text
春天        -> 应返回《春》
花草        -> 应返回《春》
少年闰土    -> 应返回《故乡》
小孩子      -> 应返回《故乡》
乡下少年    -> 应返回《故乡》
```

---

## 6. 前端模块

### 6.1 前端目录

```text
frontend/
  src/
    api/
      client.ts
      knowledge.ts
      documents.ts
      search.ts

    components/
      KnowledgeBaseList.tsx
      DocumentUploader.tsx
      SearchPanel.tsx
      StreamingResult.tsx

    App.tsx
    main.tsx

  package.json
  vite.config.ts
```

### 6.2 前端页面结构

建议单页完成：

```text
左侧：知识库列表
中间：文本输入 / txt 上传
右侧：搜索框 / 流式结果
```

必须支持：

```text
1. 创建知识库
2. 查看知识库列表
3. 选择知识库
4. 上传 txt 文件
5. 直接输入文本
6. 输入 query 搜索
7. 流式展示结果
```

不建议做：

```text
1. 登录注册
2. 权限系统
3. 复杂后台菜单
4. 富文本编辑器
5. 复杂数据看板
```

### 6.3 流式展示

前端用：

```text
fetch + ReadableStream
```

不要优先用 `EventSource`，因为搜索一般是 POST 请求。

---

## 7. MCP Server 模块

### 7.1 MCP Server 目录

```text
mcp-server/
  server.py
  tools.py
  requirements.txt
  .env.example
```

### 7.2 MCP Tool 设计

必做工具：

```text
search_knowledge_base
```

输入：

```json
{
  "query": "春天相关内容",
  "knowledge_base_id": 1,
  "top_k": 5
}
```

输出：

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

建议加分工具：

```text
list_knowledge_bases
add_text_document
```

### 7.3 MCP 调用链路

```text
Agent 输入：
帮我查一下春天相关内容

Agent 调用：
search_knowledge_base(query="春天相关内容", knowledge_base_id=1)

MCP Server：
调用 Backend /api/search

Backend：
返回语义检索结果

Agent：
根据结果组织回答
```

### 7.4 MCP 配置示例

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

---

## 8. 错误处理要求

后端需要处理：

```text
1. query 为空
2. knowledge_base_id 不存在
3. 文档内容为空
4. 文件格式不支持
5. 文件过大
6. embedding 失败
7. 向量库写入失败
8. 检索失败
9. 删除文档时向量删除失败
```

MCP Server 需要处理：

```text
1. query 为空
2. 后端服务不可用
3. 后端返回 404
4. 检索超时
5. 返回结果为空
```

推荐超时：

```text
MCP 调 Backend API timeout = 10s
```

---

## 9. 开发顺序

建议严格按下面顺序开发：

```text
1. 初始化 backend FastAPI
2. 创建 SQLite 数据库模型
3. 实现知识库 CRUD
4. 实现文档文本上传
5. 实现 txt 文件上传
6. 实现 chunk 切分
7. 接入 embedding 模型
8. 接入 ChromaDB
9. 上传文档后写入向量库
10. 实现普通语义搜索
11. 使用《春》《故乡》验证搜索结果
12. 实现流式搜索接口
13. 初始化 frontend
14. 实现知识库列表和创建
15. 实现文本上传和 txt 上传
16. 实现搜索框和流式结果展示
17. 实现 mcp-server
18. 配置 Agent 调用 MCP Tool
19. 编写测试
20. 完善 README
```

---

## 10. 测试计划

### 10.1 后端测试

```text
test_knowledge.py
- 创建知识库成功
- 查询知识库分页成功
- 更新知识库成功
- 删除知识库成功

test_upload.py
- 文本上传成功
- txt 上传成功
- 空文本失败
- 非 txt 文件失败
- 知识库不存在失败

test_search.py
- query 为空失败
- 知识库不存在失败
- 搜索“春天”返回《春》
- 搜索“少年闰土”返回《故乡》
- 搜索“小孩子”返回《故乡》
```

### 10.2 MCP 测试

```text
test_mcp_tool.py
- query 为空返回错误
- 后端不可用返回错误
- 正常 query 返回结果
- 检索超时返回错误
```

### 10.3 前端手工测试

```text
1. 创建知识库
2. 上传《春》
3. 上传《故乡》
4. 搜索“春天”
5. 搜索“少年闰土”
6. 查看流式文字是否逐步出现
```

---

## 11. 启动方式

### 11.1 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

访问：

```text
http://localhost:8000/docs
```

### 11.2 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问：

```text
http://localhost:5173
```

### 11.3 启动 MCP Server

```bash
cd mcp-server
pip install -r requirements.txt
python server.py
```

---

## 12. 面试演示流程

推荐演示顺序：

```text
1. 打开前端页面
2. 创建知识库：现代文学
3. 上传《春》
4. 上传《故乡》
5. 搜索“春天”
6. 展示返回《春》
7. 搜索“少年闰土”
8. 展示返回《故乡》
9. 搜索“小孩子”
10. 展示语义检索能力
11. 打开流式搜索
12. 展示文字逐步返回
13. 展示 MCP Server 配置
14. 让 Agent 调用 search_knowledge_base
```

面试话术：

```text
这个项目分成 Backend、Frontend 和 MCP Server 三个模块。
Backend 是业务核心，负责知识库管理、文档处理、向量化和检索。
Frontend 是轻量演示层，用于展示完整用户路径和流式返回效果。
MCP Server 是 Agent 适配层，把知识库查询能力封装成标准工具，供 Claude Code、OpenClaw 或 Hermas Agent 调用。
```

---

## 13. 后续优化方向

可以在 README 里写：

```text
1. SQLite 替换为 PostgreSQL
2. ChromaDB 替换为 Qdrant / Milvus
3. 增加 PDF / DOCX 上传
4. 增加 BM25 + 向量混合检索
5. 增加 rerank 模型
6. 接入 DeepSeek / OpenAI 生成总结回答
7. 增加用户权限和多租户隔离
8. 增加 Docker Compose 一键部署
9. 增加异步任务队列处理大文件
10. 增加检索命中引用和高亮
```

---

## 14. MVP 验收标准

项目完成后至少满足：

```text
1. 可以创建、查询、更新、删除知识库
2. 知识库列表支持分页
3. 可以直接输入文本作为知识内容
4. 可以上传 txt 文件
5. 上传后自动分块和向量化
6. 可以输入 query 做语义搜索
7. 搜索“小孩子”能匹配到《故乡》相关内容
8. 搜索“春天”能匹配到《春》相关内容
9. 搜索结果可以流式返回
10. MCP Server 提供 search_knowledge_base 工具
11. Agent 可以通过 MCP 调用工具查询知识库
12. query 为空、知识库不存在、检索失败等情况有明确错误处理
```

这份架构和交付范围非常适合技术面试：完整、可讲、可演示，也不会因为做得太大导致失控。

