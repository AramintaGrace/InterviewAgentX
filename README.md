# 🎯 InterviewAgentX — 智能面试辅助系统

基于 AI 多 Agent 协作的智能面试辅助平台，支持简历分析、智能出题、语音作答评估和面试报告生成。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python 3.12) |
| AI编排 | LangChain + LangGraph |
| 大模型 | DeepSeek API |
| 向量数据库 | Milvus 2.5 |
| 业务数据库 | PostgreSQL 17 + pgvector |
| 文件存储 | MinIO |
| 前端 | Vue 3 + TypeScript + Vite |
| 部署 | Docker Compose |

## 核心功能

- **简历分析模块**: 上传简历 → OCR识别 → 结构化解析 → AI深度分析
- **面试作答模块**: 智能出题(简历/知识库/混合) → 语音录制 → 实时语音转文字 → 多维度作答评估
- **面试报告模块**: 综合评分 → 维度分析 → 逐题回顾 → 录用建议
- **知识库模块**: 问答CRUD → 向量化 → 混合检索
- **面试记录模块**: 历史记录查询 → 简历与报告归档

## 快速开始

### 前置要求
- Docker & Docker Compose
- DeepSeek API Key
- OpenAI API Key (用于 Embedding)

### 启动

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API Keys

# 2. 启动所有服务
make up

# 3. 初始化 Milvus 集合
make init-milvus

# 4. 运行数据库迁移
make migrate
```

### 访问

- 前端界面: http://localhost:8080
- API 文档: http://localhost:8000/docs
- MinIO 控制台: http://localhost:9001

## 项目结构

```
InterviewAgentX/
├── backend/           # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/    # REST API + WebSocket 端点
│   │   ├── agents/    # Agent 提示词模板
│   │   ├── graph/     # LangGraph 工作流
│   │   ├── models/    # SQLAlchemy ORM
│   │   ├── schemas/   # Pydantic 模型
│   │   ├── services/  # 业务逻辑层
│   │   └── rag/       # RAG 检索
│   └── alembic/       # 数据库迁移
├── frontend/          # Vue 3 前端
│   └── src/
│       ├── views/     # 页面组件
│       ├── components/# 可复用组件
│       ├── stores/    # Pinia 状态管理
│       ├── api/       # API 客户端
│       ├── composables/ # 组合式函数
│       └── types/     # TypeScript 类型
├── scripts/           # 初始化脚本
├── docker-compose.yml
└── Makefile
```

## API 概览

| 模块 | 端点 |
|------|------|
| 简历 | `POST /api/v1/resumes/upload` `GET /api/v1/resumes/{id}` `POST /api/v1/resumes/{id}/analyze` |
| 面试 | `POST /api/v1/interviews` `GET /api/v1/interviews/{id}` `POST /api/v1/interviews/{id}/start` |
| 题目 | `GET /api/v1/interviews/{id}/questions` `POST /api/v1/interviews/{id}/questions/generate` |
| 答案 | `POST /api/v1/interviews/{id}/answers` `GET /api/v1/interviews/{id}/answers/{aid}/analysis` |
| 报告 | `GET /api/v1/reports/{session_id}` |
| 知识库 | `CRUD /api/v1/knowledge-base/items` `CRUD /api/v1/knowledge-base/categories` |
| 记录 | `GET /api/v1/records` `GET /api/v1/records/{candidate_id}` |
| STT | `WS /ws/stt/{session_id}/{question_id}` |
