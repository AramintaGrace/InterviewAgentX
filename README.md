# InterviewAgentX — 智能面试辅助系统

基于LangChain+ LangGraph的全流程面试辅助平台，涵盖简历上传与 OCR 解析、AI 简历评估、多模式面试作答（简历/知识库/混合出题）、LLM-as-a-Judge 答案评分、面试报告生成、候选人档案管理与知识库向量化管理。

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?logo=langchain&logoColor=white)![LangGraph](https://img.shields.io/badge/LangGraph-0.2-1C3C3C?logo=langchain&logoColor=white)![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)![Vue](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vuedotjs&logoColor=white)![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white)![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)![Milvus](https://img.shields.io/badge/Milvus-2.5-00A3E0?logo=milvus&logoColor=white)![MinIO](https://img.shields.io/badge/MinIO_S3-C72C48?logo=minio&logoColor=white)![DeepSeek](https://img.shields.io/badge/DeepSeek-API-536DFE?logo=deepseek&logoColor=white)![License](https://img.shields.io/badge/License-GPL%203.0-blue.svg)

## 技术栈

### 后端

- **Python 3.11+** · FastAPI · Pydantic Settings
- **SQLAlchemy 2.0** Async + PostgreSQL 17 + pgvector
- **LangChain** + **LangGraph** (工作流编排)
- **Pymilvus** (向量数据库)
- **MinIO** (对象存储)
- **httpx** · asyncpg · Alembic

### 前端

- **Vue 3** · TypeScript · Vite
- **Pinia** (状态管理) · **Vue Router** (路由)
- **Axios** (HTTP 客户端)
- **MediaRecorder API** (浏览器录音)

## 项目亮点

**🎯 三种面试出题模式，灵活适配不同场景**

- **简历模式**：LLM 深度阅读简历，自动生成个性化技术追问 + STAR 行为面试题
- **知识库模式**：从企业自有题库中按分类精准抽取，保证题目质量和一致性
- **混合模式**：简历题与题库题按任意比例混合，可调节占比滑块实时预览

**🧠 LLM-as-a-Judge + RAG 混合双引擎评估**

- 简历题采用四维 LLM 裁判评分（真实性/完整性/表达清晰度/技术深度），含真实性一致性检测（与简历是否矛盾）
- 知识库题采用 RAG 混合评估（标准答案覆盖分析 + 遗漏得分点识别 + 向量相似度），无参考答案时自动降级为 Judge 模式
- 每道题提交后即时展示分析面板，面试全程可回顾

**📋 题目池机制 — 面试官精准控题**

- KB/混合模式下可从已向量化的知识库条目中勾选必考题目
- 支持按关键词搜索 + 分类筛选，已选题目进入"题目池"保证必然出现

**📄 端到端简历处理流水线**

- 上传 → MinIO 存储 → 硅基流动 DeepSeek-OCR（Files API 直传 + 循环输出自动去重）→ DeepSeek-Chat 结构化信息提取 → 自动创建候选人档案
- OCR 失败自动重试，图片过大自动压缩，HTML/Markdown 标签清洗，重复行智能去重

**📊 完整的面试报告生成**

- DeepSeek-Reasoner 综合所有答案分析，生成结构化报告：综合评分、五维能力评估、逐题回顾、优势/待提升标签、详细反馈
- 报告持久化存储，候选人档案页可随时回溯

**🗄️ 知识库全生命周期管理**

- 题目 CRUD + 分类管理 + 向量化状态追踪（已向量化/未向量化/待重新向量化）
- 批量操作：批量修改分类、批量删除、批量向量化
- 答案修改后自动标记"待重新向量化"，支持按向量化状态筛选

**🎙️ 浏览器录音 + 硅基流动 STT 实时转写**

- 基于 MediaRecorder API 的浏览器端录音，停止后自动上传至硅基流动 FunAudioLLM/SenseVoiceSmall 转写
- 支持手动编辑转写结果，语音与文字混合输入

**🔍 候选人档案一站式管理**

- 面试记录表格（评分/日期/筛选/搜索）→ 点击进入完整档案
- 档案页一站式查看：候选人信息 + 简历图片预览 + OCR 解析信息 + AI 分析详情（技能评分/项目亮点/建议面试题/风险提示）+ 面试历史 + 报告详情（维度评分/逐题回顾）
- 支持级联删除候选人全部数据（含确认对话框）

**🛡️ 全链路错误处理**

- 后端 8 个全局异常处理器，结构化返回 `{ detail, code }`
- 前端 Axios 拦截器统一提取 HTTP 状态码 + 错误消息
- 前端各操作点均有 ErrorBanner / 成功提示 / 加载状态

## 架构总览

```
┌──────────────────────────────────────────────────────┐
│  Vue 3 + TypeScript + Pinia + Vite (Frontend)        │
│  简历上传 · 面试作答 · 报告展示 · 知识库 · 记录管理   │
├──────────────────────────────────────────────────────┤
│  FastAPI + SQLAlchemy Async + LangChain (Backend)    │
│  文档解析 · OCR · 问题生成 · 答案评估 · 报告生成     │
├───────────────┬───────────────┬──────────────────────┤
│  PostgreSQL   │    Milvus     │       MinIO          │
│  业务数据     │  向量检索     │  简历/音频存储       │
│  LangGraph    │  Embedding    │  S3 兼容             │
│  Checkpointer │  COSINE相似度 │                      │
└───────────────┴───────────────┴──────────────────────┘
```

**外部 AI 服务**

| 服务 | 平台 | 模型 |
|---|---|---|
| LLM 对话/推理 | DeepSeek API | `deepseek-chat` · `deepseek-reasoner` |
| 向量嵌入 | 硅基流动 SiliconFlow | `Qwen/Qwen3-Embedding-8B` (4096 维) |
| 语音转文本 | 硅基流动 SiliconFlow | `FunAudioLLM/SenseVoiceSmall` |
| OCR 文字识别 | 硅基流动 SiliconFlow | `deepseek-ai/DeepSeek-OCR` |

## 功能模块

### 1. 简历分析

- 上传简历（PDF / Word / 图片），存储至 MinIO
- DeepSeek-OCR 多模态识别，提取文字并后处理去重
- DeepSeek-Chat 解析结构化信息（姓名/联系方式/教育/工作/技能/项目）
- DeepSeek-Chat 生成 AI 简历分析报告（优势/不足/技能评分/项目亮点/建议面试题/风险提示）
- 识别出的候选人自动创建档案

### 2. 面试作答（三种模式）

| 模式 | 出题方式 | 答案评估 |
|---|---|---|
| **简历模式** | LLM 根据简历 OCR 深度分析生成结构化题目 | LLM-as-a-Judge 四维评分（真实性/完整性/表达清晰度/技术深度） |
| **知识库模式** | 从已向量化的知识库条目随机抽取或按分类/题目池指定 | RAG 混合评估（标准答案对比 + 覆盖/遗漏分析），无参考时降级为 Judge |
| **混合模式** | 简历 LLM + 知识库 按比例混合，交错排列，支持题目池 | 按题源自动选择 Judge 或 RAG 模式 |

- 录音 + 硅基流动 STT 实时转写，支持手动编辑
- 每题提交后展示分析面板（得分/维度/评语/改进建议/真实性判断）
- 未提交不可进入下一题，提交后不可重复提交
- 题目池：从 KB 中指定必考题目

### 3. 面试报告

- 面试结束后一键生成报告
- DeepSeek-Reasoner 综合所有答案分析生成结构化报告：
  - 综合评分 + 录用建议
  - 能力维度评分（技术能力/沟通表达/问题解决/经验匹配/文化契合）
  - 逐题回顾（题目/得分/评价）
  - 优势/待提升标签 + 详细综合反馈

### 4. 知识库

- 分类管理（增删改查 + 条目计数 + 级联/保留删除）
- 条目 CRUD（题目/问题/答案/标签/难度）
- 向量化管理：创建时自动生成 Embedding 写入 Milvus
- 三种向量化状态：已向量化 · 未向量化 · 待重新向量化（答案修改后）
- 批量操作：批量修改分类 · 批量删除 · 批量向量化
- 按关键词/分类/向量化状态筛选 + 分页

### 5. 面试记录

- 候选人维度的面试档案
- 表格展示（姓名/联系方式/日期/评分）+ 筛选搜索
- 点击展开完整档案：候选人信息 + 简历图片预览 + 解析信息 + AI 分析详情 + 面试历史 + 报告详情（维度评分/逐题回顾）
- 删除操作：级联清除候选人全部数据（含确认对话框）

## 快速开始

### 环境要求

- Docker & Docker Compose
- Python 3.11+
- Node.js 22+
- Poetry（Python 依赖管理）

### 1. 克隆项目

```bash
git clone <repo-url>
cd InterviewAgentX
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 DeepSeek 和硅基流动 API Key
```

需要申请以下 API Key：

- **DeepSeek API**：https://platform.deepseek.com/api_keys — 用于 LLM 对话和推理
- **硅基流动 SiliconFlow**：https://cloud.siliconflow.cn — 用于 Embedding、STT、OCR

### 3. 启动基础设施（Docker）

```bash
docker compose up -d postgres etcd minio milvus
```

等待所有服务健康检查通过（约 30-60 秒）：

```bash
docker compose ps
# 应显示 postgres、etcd、minio、milvus 均为 healthy
```

初始化 Milvus 向量库：

```bash
docker compose run --rm -e EMBEDDING_DIM=4096 milvus-init
```

### 4. 安装依赖 & 启动后端

```bash
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端 API 运行在 http://localhost:8000，API 文档 http://localhost:8000/docs

### 5. 安装依赖 & 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:5173

### 6. 一键开发环境（Docker 全栈）

```bash
# 仅基础设施
docker compose up -d postgres etcd minio milvus

# 或全部（backend + frontend 也 Docker 化）
docker compose up -d
```

## 项目结构

```
InterviewAgentX/
├── backend/
│   ├── app/
│   │   ├── agents/              # Agent 工厂 + Prompt 模板
│   │   │   ├── agent_factory.py     # DeepSeek LLM/Rasoner 工厂
│   │   │   ├── structured_output.py # JSON 解析 + 降级处理
│   │   │   └── prompts/             # 各 Agent Prompt 模板
│   │   ├── api/v1/              # REST API 路由
│   │   │   ├── resumes.py          # 简历上传/OCR/分析
│   │   │   ├── interviews.py       # 面试会话 CRUD
│   │   │   ├── questions.py        # 题目生成 (resume/KB/mixed)
│   │   │   ├── answers.py          # 回答提交 + AI 分析
│   │   │   ├── reports.py          # 报告生成/查询
│   │   │   ├── knowledge_base.py   # KB CRUD + 批量操作
│   │   │   ├── records.py          # 候选人档案 + 删除
│   │   │   ├── stt.py              # 语音转文本 REST
│   │   │   └── websocket.py        # STT WebSocket
│   │   ├── graph/               # LangGraph 工作流
│   │   ├── models/              # SQLAlchemy ORM 模型
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── services/            # 业务逻辑层
│   │   │   ├── resume_service.py    # 简历处理
│   │   │   ├── ocr_service.py       # OCR (SF Files API 上传 + 去重)
│   │   │   ├── embedding_service.py # 向量嵌入
│   │   │   ├── milvus_service.py    # Milvus CRUD
│   │   │   ├── minio_service.py     # MinIO 文件存储
│   │   │   ├── stt_service.py       # 硅基流动 STT
│   │   │   └── knowledge_base_service.py  # KB 双写 + 批量操作
│   │   ├── db/                  # PostgreSQL 连接
│   │   ├── utils/               # 异常/日志/代理
│   │   ├── config.py            # Pydantic Settings
│   │   ├── dependencies.py      # FastAPI 依赖注入
│   │   └── main.py              # 应用入口 + 全局异常处理
│   ├── alembic/                 # 数据库迁移
│   └── tests/                   # 单元测试
├── frontend/
│   ├── src/
│   │   ├── api/                 # Axios API 客户端
│   │   ├── components/          # Vue 组件
│   │   │   ├── resume/             # 简历上传/信息卡片/分析面板
│   │   │   ├── interview/          # 题目卡片/录音/转写/分析/进度/题目池
│   │   │   ├── report/             # 报告摘要/雷达图/逐题回顾
│   │   │   ├── knowledge-base/     # KB 卡片/搜索/分类树
│   │   │   ├── records/            # 记录表格/筛选器
│   │   │   ├── layout/             # 侧边栏
│   │   │   └── common/             # 加载/错误/确认/空状态
│   │   ├── composables/         # 录音/WebSocket/流式转写
│   │   ├── router/              # Vue Router 路由配置
│   │   ├── stores/              # Pinia 状态管理
│   │   ├── types/               # TypeScript 类型定义
│   │   └── views/               # 页面组件
│   ├── Dockerfile
│   └── vite.config.ts
├── scripts/                     # init_db.sql / init_milvus.py
├── docker-compose.yml           # 生产环境
├── docker-compose.dev.yml       # 开发环境 (热重载)
├── Makefile
└── .env.example
```

## API 路由总览

### 简历 `/api/v1/resumes`

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/upload` | 上传简历文件 (MinIO + OCR) |
| `GET` | `/{id}/ocr` | 查询 OCR 状态 |
| `POST` | `/{id}/analyze` | 触发 AI 简历分析 |
| `GET` | `/{id}/analysis` | 获取分析结果 |
| `GET` | `/{id}/file` | 获取简历文件下载链接 |

### 面试 `/api/v1/interviews`

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/` | 创建面试会话 |
| `POST` | `/{id}/start` | 启动面试 |
| `GET` | `/{id}/questions` | 获取题目列表 |
| `POST` | `/{id}/questions/generate` | 生成题目 (resume/KB/mixed) |
| `POST` | `/{id}/answers` | 提交回答 |
| `POST` | `/{id}/answers/{aid}/analyze` | AI 分析答案 |
| `GET` | `/{id}/answers/{aid}/analysis` | 获取分析结果 |
| `GET` | `/{id}/state` | 面试状态 |

### 报告 `/api/v1/reports`

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/{session_id}` | 获取报告 |
| `POST` | `/{session_id}/generate` | 生成报告 |

### 知识库 `/api/v1/knowledge-base`

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET/POST` | `/categories` | 分类列表/创建 |
| `PUT/DELETE` | `/categories/{id}` | 更新/删除分类 |
| `GET` | `/items` | 条目列表 (支持筛选+分页) |
| `POST` | `/items` | 创建条目 (含向量化) |
| `PUT/DELETE` | `/items/{id}` | 更新/删除条目 |
| `POST` | `/items/{id}/revectorize` | 重新向量化 |
| `POST` | `/items/batch/category` | 批量修改分类 |
| `POST` | `/items/batch/delete` | 批量删除 |
| `POST` | `/items/batch/revectorize` | 批量向量化 |

### 记录 `/api/v1/records`

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/` | 面试记录列表 |
| `GET` | `/{candidate_id}` | 候选人完整档案 |
| `DELETE` | `/{candidate_id}` | 级联删除候选人数据 |

### 语音 `/api/v1/stt`

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/transcribe` | 上传音频，返回转写文字 |

## 题目生成模式说明

### `source: "resume"`

LLM 根据简历 OCR 文本和 AI 分析结果生成结构化题目，包含 `source_resume_context` 和 `ai_reference_answer`。

### `source: "knowledge_base"`

```json
{
  "source": "knowledge_base",
  "count": 5,
  "kb_configs": [
    { "category_id": "<cat-uuid>", "count": 3 },
    { "category_id": null, "count": 2 }
  ],
  "pool_ids": ["<kb-item-uuid>", ...]
}
```

- `kb_configs` 为空 → 从全部分类随机
- `pool_ids` 指定必考题目（已向量化的 KB 条目）

### `source: "mixed"`

```json
{
  "source": "mixed",
  "count": 6,
  "resume_ratio": 60,
  "kb_configs": [...],
  "pool_ids": [...]
}
```

- `resume_ratio=60` → 60% 简历题 + 40% 知识库题，交错排列

## 答案评估模式

| 题目来源 | 评估模式 | 评分维度 |
|---|---|---|
| `resume_experience` / `resume_project` | LLM-as-a-Judge | 真实性 / 完整性 / 表达清晰度 / 技术深度 → 综合评分 |
| `knowledge_base` | RAG 混合评估 | 标准答案覆盖/遗漏分析 + 向量相似度 → 综合评分 |

KB 题目无参考答案时自动降级为 LLM-as-a-Judge。

## License

GPL-3.0 — GNU General Public License v3.0
