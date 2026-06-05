# InterviewAgentX — 智能面试辅助系统

基于LangChain+ LangGraph的全流程面试辅助平台，涵盖简历上传与 OCR 解析、AI 简历评估、多模式面试作答（简历/知识库/混合出题）、LLM-as-a-Judge 答案评分、面试报告生成、候选人档案管理与知识库向量化管理。

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?logo=langchain&logoColor=white)![LangGraph](https://img.shields.io/badge/LangGraph-0.2-1C3C3C?logo=langchain&logoColor=white)![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)![Vue](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vuedotjs&logoColor=white)![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white)![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)![Milvus](https://img.shields.io/badge/Milvus-2.5-00A3E0?logo=milvus&logoColor=white)![MinIO](https://img.shields.io/badge/MinIO_S3-C72C48?logo=minio&logoColor=white)![DeepSeek](https://img.shields.io/badge/DeepSeek-API-536DFE?logo=deepseek&logoColor=white)![Multi-Agent](https://img.shields.io/badge/Multi--Agent-Tool%20Calling-8B5CF6)![Agentic RAG](https://img.shields.io/badge/Agentic_RAG-Hybrid%2BRRF-EC4899)![License](https://img.shields.io/badge/License-GPL%203.0-blue.svg)

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

**🤖 多智能体协作架构 (Multi-Agent System)**

- 5 个专业化 AI Agent（Orchestrator / ResumeAnalyst / QuestionCurator / AnswerEvaluator / ReportSynthesizer），每个 Agent 拥有独立工具集
- Orchestrator 动态路由：根据面试状态、答案质量、错误条件自主决策下一步
- 自适应难度调整 + 追问注入 + 错误恢复自动降级
- 完整审计追踪：每个 Agent 记录决策、工具调用、token 消耗、执行时长
- 通过 `MULTI_AGENT_ENABLED` 环境变量切换，默认关闭保证向后兼容

**🔍 Agentic RAG 智能检索**

- 7 步 LLM 驱动检索循环：DECIDE（是否检索）→ FORMULATE（生成查询）→ EXECUTE（多策略搜索）→ EVALUATE（评判相关性）→ RE-RETRIEVE（重检索）→ SYNTHESIZE（综合说明）→ CITE（来源引用）
- 混合检索引擎：Dense (Milvus COSINE) + Sparse (PostgreSQL FTS) + RRF 融合 (k=60)
- LLM 交叉编码重排序器：逐对评分重排，失败自动降级为 COSINE 相似度
- 三种检索策略按场景自动选择，全面提升召回率和精确率

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

### 系统架构

```
┌──────────────────────────────────────────────────────────────────┐
│  Vue 3 + TypeScript + Pinia + Vite (Frontend)                    │
│  简历上传 · 面试作答 · 报告展示 · 知识库 · 记录管理              │
├──────────────────────────────────────────────────────────────────┤
│  FastAPI + SQLAlchemy Async + LangChain + LangGraph (Backend)    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Orchestrator Agent (多智能体调度器)                      │   │
│  │  ┌──────────┐ ┌──────────────┐ ┌───────────────┐        │   │
│  │  │ Resume   │ │ Question     │ │ Answer        │        │   │
│  │  │ Analyst  │ │ Curator      │ │ Evaluator     │        │   │
│  │  │ 简历分析 │ │ 题目生成     │ │ 答案评估      │        │   │
│  │  └──────────┘ └──────────────┘ └───────────────┘        │   │
│  │  ┌──────────────┐                                        │   │
│  │  │ Report       │                                        │   │
│  │  │ Synthesizer  │                                        │   │
│  │  │ 报告合成     │                                        │   │
│  │  └──────────────┘                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Agentic RAG 检索层                                       │   │
│  │  AgenticRetriever → HybridRetriever → Reranker           │   │
│  │  7步检索决策 · 稠密+稀疏混合 · LLM 交叉编码重排序        │   │
│  └──────────────────────────────────────────────────────────┘   │
├───────────────┬───────────────┬──────────────────────────────────┤
│  PostgreSQL   │    Milvus     │       MinIO                      │
│  业务数据     │  向量检索     │  简历/音频存储                  │
│  LangGraph    │  Embedding    │  S3 兼容                         │
│  Checkpointer │  COSINE相似度 │                                  │
│  FTS 全文搜索 │               │                                  │
└───────────────┴───────────────┴──────────────────────────────────┘
```

### 双模式工作流

系统支持两种工作流模式，通过 `MULTI_AGENT_ENABLED` 环境变量切换：

| 模式 | 工作流 | 特点 |
|---|---|---|
| **单智能体模式** (默认) | `简历分析 → 题目生成 → 答题 → 答案评估 → [下一题|生成报告]` | 线性固定流程，稳定可靠 |
| **多智能体模式** | `Orchestrator → Agent → Orchestrator → Agent → ...` | 动态路由，自主决策，自适应难度 |

**多智能体模式工作流：**

```
START → Orchestrator → ResumeAnalyst → Orchestrator → QuestionCurator
     → Orchestrator → [答题] → Orchestrator → AnswerEvaluator
     → Orchestrator → ReportSynthesizer → Orchestrator → END
```

Orchestrator 根据面试状态、答案质量和错误情况动态决定下一步，支持：
- 自适应难度调整（根据答题表现升高/降低难度）
- 追问注入（回答不充分时自动生成追问）
- 错误恢复（智能体失败时自动降级为线性路由）

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

## 高级架构详解

### 多智能体系统 (Multi-Agent System)

系统内置 5 个专业化 AI Agent，每个 Agent 拥有独立的工具集和系统提示词，通过 LangGraph 状态图编排协作。

#### Orchestrator Agent（调度智能体）

面试流程的主控中心，负责：

- **状态监控**：通过 `get_state_summary` 获取当前面试全貌（阶段、进度、分数）
- **质量评估**：通过 `check_answer_quality` 评估已回答质量，决定是否需要追问
- **难度调整**：通过 `adjust_difficulty` 根据表现动态升高或降低后续题目难度
- **路由决策**：输出 `{"next_action": ..., "phase": ..., "reasoning": ..., "params": ...}` 决定下一步

**路由决策类型：**
| `next_action` | 说明 |
|---|---|
| `continue` | 继续当前阶段，进入下一节点 |
| `retry` | 重新执行当前阶段（如 OCR 失败重试） |
| `skip` | 跳过当前阶段（如简历无内容时跳过分析） |
| `inject_followup` | 注入追问（当前回答不够充分） |
| `adjust_difficulty` | 调整难度后继续 |
| `abort` | 异常终止（连续错误超过阈值） |

#### Resume Analyst Agent（简历分析智能体）

- **工具**：`get_full_resume_text` · `query_candidate_history` · `flag_inconsistency`
- **输出 8 维分析**：
  - `overall_assessment` — 综合评估
  - `strengths` — 技术优势列表
  - `weaknesses` — 待提升领域
  - `skill_match` — 技能匹配度（按技能逐一评分）
  - `experience_relevance_score` — 经验相关度评分（1-10）
  - `project_highlights` — 项目亮点提取
  - `suggested_questions` — 建议面试题目
  - `red_flags` — 风险提示（经历矛盾、技能夸大等）
- 支持候选人历史档案查询，发现重复申请和技能演进

#### Question Curator Agent（题目生成智能体）

- **工具**：`search_knowledge_base` (Agentic RAG) · `get_resume_analysis` · `get_kb_categories`
- **三种生成模式**：
  - `resume` — 基于简历深度分析生成个性化题目
  - `knowledge_base` — 从知识库精准检索 + 按分类/题目池抽取
  - `mixed` — 简历题与题库题按比例混合，交错排列
- 使用 Agentic RAG 自主决策：是否检索、检索什么、检索结果是否足够、是否需要重新检索
- 每道题携带 `source_resume_context`（出题依据）和 `ai_reference_answer`（AI 参考答案）

#### Answer Evaluator Agent（答案评估智能体）

- **双模式自动选择**（根据题目来源）：
  - **LLM Judge 模式**（简历题）：
    - 工具：`check_resume_consistency` — 检测回答与简历是否矛盾
    - 四维评分：**真实性** (1-5) · **完整性** (1-5) · **表达清晰度** (1-5) · **技术深度** (1-5)
    - 输出：综合评分 + 各维度评语 + 真实性判断 + 改进建议
  - **RAG Hybrid 模式**（知识库题）：
    - 工具：`retrieve_reference_answer` · `search_knowledge_base_for_fact_check`
    - 标准答案覆盖分析：`covered_points` + `missing_points`
    - 无参考答案时自动降级为 LLM Judge 模式
- **鲁棒解析**：支持 6+ 种不同输出格式的自动识别与正则提取

#### Report Synthesizer Agent（报告合成智能体）

- **工具**：`collect_all_analyses` · `compute_dimension_scores`
- 使用 **DeepSeek Reasoner** 进行深度推理合成
- **输出**：
  - `overall_score` — 综合评分 (1-100)
  - `dimension_scores` — 五维能力评估（技术能力/沟通表达/问题解决/经验匹配/文化契合）
  - `question_reviews` — 逐题回顾（含得分与评语）
  - `strengths` / `weaknesses` — 优势/待提升标签
  - `hiring_recommendation` — 录用建议
  - `detailed_feedback` — 详细综合反馈

#### 智能体工具架构

所有工具通过闭包注入 `state_provider: Callable[[], Dict]` 访问工作流状态，按智能体组织：

```
tools.py
├── create_resume_analyst_tools()
│   ├── get_full_resume_text        — 获取简历 OCR 全文
│   ├── query_candidate_history     — 查询候选人历史面试记录
│   └── flag_inconsistency          — 标记简历矛盾点
├── create_question_curator_tools()
│   ├── search_knowledge_base       — Agentic RAG 知识库检索
│   ├── get_resume_analysis         — 获取简历分析结果
│   └── get_kb_categories           — 获取知识库分类列表
├── create_answer_evaluator_tools()
│   ├── retrieve_reference_answer   — 获取标准参考答案
│   ├── check_resume_consistency    — 检测与简历的一致性
│   └── search_knowledge_base_for_fact_check — 事实核查检索
├── create_report_synthesizer_tools()
│   ├── collect_all_analyses        — 收集所有答案分析结果
│   └── compute_dimension_scores    — 计算五维能力评分
└── create_orchestrator_tools()
    ├── get_state_summary            — 获取面试状态摘要
    ├── check_answer_quality         — 评估答案质量
    └── adjust_difficulty            — 调整面试难度
```

#### 智能体审计追踪

每个 Agent 执行后生成 `AgentTrace`，记录完整决策过程：

```json
{
  "agent_name": "QuestionCurator",
  "phase": "question_generation",
  "decisions": ["search_knowledge_base('Python 多线程')", "accept_results"],
  "tool_calls": [{"tool": "search_knowledge_base", "args": {...}, "result_summary": "..."}],
  "iterations": 2,
  "tokens_used": {"input": 1500, "output": 800},
  "duration_ms": 3200,
  "success": true
}
```

### Agentic RAG 检索系统

#### 7 步智能检索循环

AgenticRetriever 不盲目检索，而是通过 LLM 驱动每一步决策：

```
用户查询
  │
  ├─[1] DECIDE    — LLM 判断是否需要检索（闲聊/已有足够上下文则跳过）
  ├─[2] FORMULATE — LLM 生成最优检索查询（扩展缩写、补充上下文、多角度改写）
  ├─[3] EXECUTE   — 多策略搜索（稠密+稀疏+混合，委托 HybridRetriever）
  ├─[4] EVALUATE  — LLM 评判每条结果的与查询的相关性 (0-1)
  ├─[5] RE-RETRIEVE — 相关性低于阈值 (0.65) 时重新表述查询再检索（最多重试 1 次）
  ├─[6] SYNTHESIZE — LLM 综合说明检索结果为何相关
  └─[7] CITE      — 标明引用的知识库条目 ID
```

**配置参数：**

| 参数 | 默认值 | 说明 |
|---|---|---|
| `AGENTIC_RAG_RELEVANCE_THRESHOLD` | 0.65 | 最低相关性阈值 |
| `AGENTIC_RAG_MAX_RETRIES` | 1 | 最大重新检索次数 |
| `AGENTIC_RAG_TOP_K` | 5 | 单次检索返回数量 |

#### 混合检索引擎 (HybridRetriever)

三种检索策略，覆盖不同搜索场景：

| 策略 | 技术 | 适用场景 |
|---|---|---|
| **Dense (稠密)** | Milvus COSINE 向量相似度 | 语义搜索，理解同义词和概念 |
| **Sparse (稀疏)** | PostgreSQL `tsvector`/`tsquery` 全文搜索 | 精确关键词匹配，专业术语 |
| **Hybrid (混合)** | RRF (Reciprocal Rank Fusion, k=60) | 融合两者优势，全面提升召回率 |

#### LLM 重排序器 (Reranker)

- 基于 LLM 的交叉编码器（Cross-Encoder）重排序
- 对每个 `(query, document)` 对进行逐对评分
- 支持 `question`/`answer`/`title`/`text` 多种文档字段格式
- LLM 不可用时自动降级为 COSINE 相似度排序

### 图工作流架构 (LangGraph)

#### 状态定义 (InterviewState)

```
InterviewState
├── session_id: str                    # 面试会话 UUID
├── thread_id: str                     # LangGraph 线程 ID
├── current_phase: Phase               # 8 个阶段枚举
├── question_index: int               # 当前题目索引
├── resume_ocr: List[str]             # 简历 OCR 文本
├── resume_analyses: List[dict]       # 简历分析结果
├── questions: List[GeneratedQuestion] # 面试题目列表
├── answers: List[AnswerData]         # 候选回答
├── answer_analyses: List[dict]       # 答案评估结果
├── interview_report: dict            # 面试报告
├── errors: List[str]                 # 错误日志
├── orchestrator_decision: dict       # 调度器决策
├── agent_traces: List[AgentTrace]    # 智能体审计追踪
├── pending_follow_ups: List[dict]    # 待追问列表
├── interview_difficulty: str         # 当前难度 (easy/medium/hard)
├── kb_retrieval_cache: dict          # 知识库检索缓存
└── resilience_context: dict          # 容错上下文
```

所有列表字段使用 LangGraph `Annotated[list, operator.add]` 追加语义。

#### 关键节点

| 节点 | 单智能体模式 | 多智能体模式 |
|---|---|---|
| `orchestrator_node` | 线性路由（按 Phase 顺序） | InterviewOrchestratorAgent + 工具 → 动态决策 |
| `resume_analysis_node` | LLM 单次调用 | ResumeAnalystAgent + 3 工具 |
| `question_generation_node` | LLM 单次调用 | QuestionCuratorAgent + Agentic RAG |
| `answer_analysis_node` | LLM 单次调用（始终如此，最快路径） | LLM 单次调用 |
| `report_generation_node` | DeepSeek Reasoner | ReportSynthesizerAgent + 2 工具 |

#### 条件路由

- `route_after_answer_analysis()` — 根据 `pending_follow_ups`、错误阈值、`orchestrator_decision` 决定进入下一题或生成报告
- `route_question_generation()` — 根据题目来源类型路由到不同生成逻辑
- `_route_orchestrator()` — 多智能体模式下的调度器路由

#### 状态持久化

- 使用 `AsyncPostgresSaver`（基于 PostgreSQL）实现 LangGraph Checkpointer
- 面试状态可跨请求恢复，支持断点续面
- 长会话自动持久化，避免状态丢失

## 配置参考

### 环境变量完整列表

#### LLM & AI 服务

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DEEPSEEK_API_KEY` | — | DeepSeek API 密钥（必填） |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | DeepSeek API 地址 |
| `DEEPSEEK_MODEL_CHAT` | `deepseek-chat` | 对话模型 |
| `DEEPSEEK_MODEL_REASONER` | `deepseek-reasoner` | 推理模型（报告生成） |
| `EMBEDDING_API_KEY` | — | 硅基流动 API Key |
| `EMBEDDING_BASE_URL` | `https://api.siliconflow.cn/v1` | 嵌入服务地址 |
| `EMBEDDING_MODEL` | `Qwen/Qwen3-Embedding-8B` | 嵌入模型 |
| `EMBEDDING_DIM` | `4096` | 向量维度 |
| `OCR_API_KEY` | — | OCR API Key |
| `OCR_BASE_URL` | `https://api.siliconflow.cn/v1` | OCR 服务地址 |
| `OCR_MODEL` | `deepseek-ai/DeepSeek-OCR` | OCR 模型 |
| `STT_API_KEY` | — | 语音转文本 API Key |
| `STT_BASE_URL` | `https://api.siliconflow.cn/v1` | STT 服务地址 |
| `STT_MODEL` | `FunAudioLLM/SenseVoiceSmall` | STT 模型 |

#### 基础设施

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL 连接串 |
| `DATABASE_URL_SYNC` | `postgresql+psycopg2://...` | 同步连接串（Alembic） |
| `MILVUS_HOST` | `localhost` | Milvus 主机 |
| `MILVUS_PORT` | `19530` | Milvus 端口 |
| `MILVUS_COLLECTION` | `knowledge_base_vectors` | 向量集合名 |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO 地址 |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO 访问密钥 |
| `MINIO_SECRET_KEY` | `minioadmin` | MinIO 密钥 |
| `MINIO_BUCKET_RESUMES` | `resumes` | 简历存储桶 |
| `MINIO_BUCKET_AUDIO` | `interview-audio` | 音频存储桶 |

#### 多智能体 & RAG

| 变量 | 默认值 | 说明 |
|---|---|---|
| `MULTI_AGENT_ENABLED` | `false` | 启用多智能体模式 |
| `AGENT_MAX_ITERATIONS` | `5` | 单智能体最大工具调用循环次数 |
| `AGENTIC_RAG_RELEVANCE_THRESHOLD` | `0.65` | Agentic RAG 最低相关性 |
| `AGENTIC_RAG_MAX_RETRIES` | `1` | 最大重新检索次数 |
| `AGENTIC_RAG_TOP_K` | `5` | 检索返回数量 |

#### 其他

| 变量 | 默认值 | 说明 |
|---|---|---|
| `ENVIRONMENT` | `development` | 运行环境 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `CORS_ORIGINS` | `http://localhost:8080` | CORS 允许来源 |
| `HTTP_PROXY` / `HTTPS_PROXY` | — | HTTP 代理 |
| `NO_PROXY` | `localhost,127.0.0.1,...` | 代理排除列表 |

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
│   │   ├── agents/                  # 多智能体系统
│   │   │   ├── base.py                 # BaseAgent 抽象基类 (工具调用循环)
│   │   │   ├── orchestrator.py         # OrchesTrator — 主控调度智能体
│   │   │   ├── resume_analyst.py       # ResumeAnalyst — 简历分析智能体
│   │   │   ├── question_curator.py     # QuestionCurator — 题目生成智能体
│   │   │   ├── answer_evaluator.py     # AnswerEvaluator — 答案评估智能体
│   │   │   ├── report_synthesizer.py   # ReportSynthesizer — 报告合成智能体
│   │   │   ├── tools.py                # 工具定义 (按智能体组织，闭包注入 state)
│   │   │   ├── agent_factory.py        # DeepSeek LLM/Reasoner 工厂
│   │   │   ├── structured_output.py    # JSON 解析 + 降级处理 (3种恢复策略)
│   │   │   └── prompts/                # 各 Agent 系统提示词模板
│   │   │       ├── orchestrator.py         # 调度器提示词
│   │   │       ├── resume_merge.py         # 简历合并提示词
│   │   │       ├── answer_analysis_kb.py   # KB 答案评估提示词
│   │   │       ├── answer_analysis_resume.py # 简历答案评估提示词
│   │   │       └── agentic_rag.py          # Agentic RAG 决策提示词
│   │   ├── rag/                     # Agentic RAG 检索引擎
│   │   │   ├── agentic_retriever.py     # 7步智能检索循环 (DECIDE→CITE)
│   │   │   ├── hybrid_retriever.py      # 混合检索 (Dense+Sparse+RRF)
│   │   │   └── reranker.py              # LLM 交叉编码重排序器
│   │   ├── graph/                   # LangGraph 工作流
│   │   │   ├── state.py                 # InterviewState 定义 (15+字段)
│   │   │   ├── workflow.py              # StateGraph 构建器 (双模式)
│   │   │   ├── checkpointer.py          # AsyncPostgresSaver 单例
│   │   │   └── nodes/
│   │   │       ├── orchestrator_node.py     # 调度器节点 (新增)
│   │   │       ├── resume_analysis_node.py  # 简历分析节点
│   │   │       ├── question_generation_node.py # 题目生成节点
│   │   │       ├── answer_analysis_node.py  # 答案评估节点
│   │   │       ├── report_generation_node.py # 报告生成节点
│   │   │       └── routing_node.py          # 条件路由逻辑
│   │   ├── api/v1/                  # REST API 路由
│   │   │   ├── resumes.py              # 简历上传/OCR/分析
│   │   │   ├── interviews.py           # 面试会话 CRUD
│   │   │   ├── questions.py            # 题目生成 (resume/KB/mixed)
│   │   │   ├── answers.py              # 回答提交 + AI 分析
│   │   │   ├── reports.py              # 报告生成/查询
│   │   │   ├── knowledge_base.py       # KB CRUD + 批量操作
│   │   │   ├── records.py              # 候选人档案 + 删除
│   │   │   ├── stt.py                  # 语音转文本 REST
│   │   │   └── websocket.py            # STT WebSocket
│   │   ├── models/                  # SQLAlchemy ORM 模型
│   │   ├── schemas/                 # Pydantic 请求/响应模型
│   │   │   ├── common.py               # 分页/错误/成功响应
│   │   │   ├── resume.py               # 简历相关模型
│   │   │   ├── interview.py            # 面试相关模型
│   │   │   ├── report.py               # 报告相关模型
│   │   │   └── knowledge_base.py       # 知识库相关模型
│   │   ├── services/                # 业务逻辑层
│   │   │   ├── resume_service.py        # 简历处理 + 候选人创建
│   │   │   ├── interview_service.py     # 面试会话生命周期
│   │   │   ├── ocr_service.py           # OCR (SF Files API 上传 + 去重)
│   │   │   ├── embedding_service.py     # 向量嵌入 (单条+批量)
│   │   │   ├── milvus_service.py        # Milvus CRUD + 混合搜索
│   │   │   ├── minio_service.py         # MinIO 文件存储
│   │   │   ├── stt_service.py           # 硅基流动 STT
│   │   │   └── knowledge_base_service.py # KB 双写(DB+Milvus) + 批量操作
│   │   ├── db/                      # PostgreSQL 连接 + 会话管理
│   │   ├── utils/                   # 异常处理器/日志/代理工具
│   │   ├── config.py                # Pydantic Settings (全环境变量)
│   │   ├── dependencies.py          # FastAPI 依赖注入 (含多智能体懒加载)
│   │   └── main.py                  # 应用入口 + 8个全局异常处理器
│   ├── alembic/                     # 数据库迁移
│   └── tests/                       # 单元测试
├── frontend/
│   ├── src/
│   │   ├── api/                     # Axios API 客户端
│   │   │   ├── client.ts               # 基础客户端 + 拦截器
│   │   │   ├── interviews.ts           # 面试 API
│   │   │   ├── resumes.ts              # 简历 API
│   │   │   ├── reports.ts              # 报告 API
│   │   │   ├── knowledgeBase.ts        # 知识库 API
│   │   │   └── stt.ts                  # 语音转文本 API
│   │   ├── components/              # Vue 组件
│   │   │   ├── resume/                 # 简历上传/信息卡片/分析面板
│   │   │   ├── interview/              # 题目卡片/录音/转写/分析/进度/题目池
│   │   │   ├── report/                 # 报告摘要/雷达图/逐题回顾
│   │   │   ├── knowledge-base/         # KB 卡片/搜索/分类树
│   │   │   ├── records/                # 记录表格/筛选器
│   │   │   ├── layout/                 # AppHeader/AppSidebar/AppFooter
│   │   │   └── common/                 # LoadingSpinner/ErrorBanner/ConfirmDialog/EmptyState
│   │   ├── composables/             # useAudioRecorder/useWebSocket/useStreamingTranscript
│   │   ├── router/                  # Vue Router 路由配置 (11条路由)
│   │   ├── stores/                  # Pinia 状态管理 (interview/knowledgeBase/stt/ui)
│   │   ├── types/                   # TypeScript 类型定义
│   │   └── views/                   # 页面组件 (10个视图)
│   ├── Dockerfile
│   └── vite.config.ts
├── scripts/                         # init_db.sql / init_milvus.py
├── docker-compose.yml               # 生产环境
├── docker-compose.dev.yml           # 开发环境 (热重载)
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
