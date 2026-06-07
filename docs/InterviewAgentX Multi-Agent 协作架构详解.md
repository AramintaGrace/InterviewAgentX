# InterviewAgentX Multi-Agent 协作架构详解

## 架构全景

整个系统基于 **LangGraph 状态机** 编排，有 **双模运行**：单 Agent 管线（默认）和 Multi-Agent 协作（`MULTI_AGENT_ENABLED=true`）。Multi-Agent 模式下，五个专业化 Agent 围绕一个共享的 `InterviewState` 工作，由一个 Orchestrator 动态调度。

```
                    ┌─────────────────────┐
                    │   Orchestrator       │
                    │  (主控协调器)         │
                    └──┬──┬──┬──┬──┬──────┘
                       │  │  │  │  │
          ┌────────────┘  │  │  │  └────────────┐
          ▼               ▼  ▼  ▼               ▼
   ResumeAnalyst   QuestionCurator  AnswerEvaluator  ReportSynthesizer
   (简历分析)      (题目策展)       (答案评估)        (报告合成)
```

Graph 拓扑（`workflow.py:63-91`，Multi-Agent 模式）：

```
START → orchestrator → [Agent] → orchestrator → [Agent] → ... → orchestrator → END
```

所有 Agent 都继承自 `BaseAgent`（`base.py`），共享同一套 **Tool-calling Loop** 模式。

---

## 一、五个 Agent 的职责与工具

### 1. ResumeAnalystAgent — 简历分析

**文件**: `resume_analyst.py` | **max_iterations**: 3

**职责**: 对候选人简历进行深度分析，挖掘优势、短板、疑点，生成结构化分析报告。

**工具** (`tools.py:43-130`):

| 工具 | 作用 |
|------|------|
| `get_full_resume_text` | 从 state 中取出完整 OCR 文本和结构化解析数据（截断到 8000 字符防止 token 溢出） |
| `query_candidate_history` | 查询候选人历史面试记录（通过 candidate_id 查 DB） |
| `flag_inconsistency` | 标记简历中的矛盾点（claim vs evidence），按 severity 分级，用于后续追问 |

**输出**: 8 维度分析 JSON — `overall_assessment`, `strengths`, `weaknesses`, `skill_match`, `experience_relevance_score`, `project_highlights`, `suggested_questions`, `red_flags`

**工作流**: 获取简历文本 → 查历史记录 → 全面分析 → 标记疑点 → 生成结构化报告

---

### 2. QuestionCuratorAgent — 题目策展

**文件**: `question_curator.py` | **max_iterations**: 5（最多，因为可能多次 RAG 重试）

**职责**: 根据简历分析 + 知识库，生成个性化面试题目。支持三种模式。

**工具** (`tools.py:133-259`):

| 工具 | 作用 |
|------|------|
| `search_knowledge_base` | **Agentic RAG** 检索 — 自动判断是否需要检索、优化查询、评估相关性、低分重检 |
| `get_resume_analysis` | 读取简历分析结果（优势/短板/技能评分），用于个性化出题 |
| `get_kb_categories` | 列出可用知识库分类，用于定向选题 |

**三种生成模式**:
- **resume**: 基于候选人项目经历生成 STAR 行为面试题和技术深挖题
- **knowledge_base**: 从知识库中选取题目，以 KB 条目的答案作为 AI 参考答案
- **mixed**: 混合两者，按配置比例交错排列

**输出**: `GeneratedQuestion[]` 列表，每道题标注 `source_type`、`source_kb_item_id`、`question_text`、`ai_reference_answer`

---

### 3. AnswerEvaluatorAgent — 答案评估

**文件**: `answer_evaluator.py` | **max_iterations**: 3

**职责**: 对候选人回答进行多维度评分。**这是唯一一个根据题目来源类型动态切换工具的 Agent**。

**关键设计**: 构造函数接收 `eval_mode` 参数（`"llm_judge"` 或 `"rag_hybrid"`），调用方在创建时**只注入与该模式匹配的工具**，防止 Agent 错误地混用工具：

```
resume_experience / resume_project → 只给 [check_resume_consistency]，不绑 RAG 工具
knowledge_base                   → 只给 [retrieve_reference_answer, search_knowledge_base_for_fact_check]
```

这比在 prompt 里写"不要用 XX 工具"更可靠——直接从工具列表里移除，Agent 根本看不到。

**工具** (`tools.py:262-422`):

| 工具 | 适用模式 | 作用 |
|------|---------|------|
| `retrieve_reference_answer` | RAG hybrid | Agentic RAG 检索知识库中的标准答案作为评分基准 |
| `check_resume_consistency` | LLM judge | 将候选人声称的内容与简历原文对比，检测矛盾 |
| `search_knowledge_base_for_fact_check` | RAG hybrid | 验证候选人回答中的技术事实 |

**LLM-as-a-Judge 模式**（简历题）: 4 维度评分 — `accuracy`（真实性）、`completeness`（完整性）、`clarity`（表达清晰度）、`technical_depth`（技术深度），每个维度 1-5 分，外加 `authenticity_flag`（consistent/inconsistent/uncertain）

**RAG Hybrid 模式**（知识课题）: 对比标准答案，输出 `covered_points`（覆盖点）、`missing_points`（遗漏点）、`vector_similarity`

---

### 4. ReportSynthesizerAgent — 报告合成

**文件**: `report_synthesizer.py` | **max_iterations**: 4

**职责**: 综合所有面试数据生成最终评估报告。使用 **DeepSeek Reasoner**（更强的推理模型）。

**工具** (`tools.py:425-543`):

| 工具 | 作用 |
|------|------|
| `collect_all_analyses` | 汇总所有题目的评估摘要（每题 score + strengths + improvements） |
| `compute_dimension_scores` | 聚合 4 个维度的分数：technical_ability、communication、problem_solving、experience_relevance |

**输出**: 完整报告 — `overall_score`（0-100）、`dimension_scores`（各维度）、`question_reviews`（逐题回顾）、`strengths`/`weaknesses`、`hiring_recommendation`（4 档：strongly_recommend / recommend / consider / not_recommend）、`detailed_feedback`（200-500 字综合评价）

---

### 5. InterviewOrchestratorAgent — 主控协调器

**文件**: `orchestrator.py` | **max_iterations**: 4

**职责**: 整个 Multi-Agent 系统的大脑——动态决定调用哪个 Agent、是否追问、是否调整难度。

**工具** (`tools.py:546-691`):

| 工具 | 作用 |
|------|------|
| `get_state_summary` | 获取面试状态快照（当前阶段、题目进度、答案数、错误数、难度） |
| `check_answer_quality` | 评估某道题的回答质量，内置决策逻辑判断是否需要追问 |
| `adjust_difficulty` | 动态调整后续题目难度（easy/medium/hard） |

---

## 二、Orchestrator 如何决策任务分配

决策不是写死的 if-else，而是 **LLM 驱动的自主决策**。整个流程如下：

### Step 1: 构建上下文消息

`orchestrator.py:66-91` 将当前 state 的关键信息打包发给 LLM：

```python
# build_user_message 构造的信息
- 阶段: current_phase (init / resume_analysis / question_generation / answering / ...)
- 题目来源: resume / knowledge_base / mixed
- 题目进度: question_index + 1 / total_questions
- 已提交答案数、已完成分析数
- 错误数、简历是否已分析、题目是否已生成
```

### Step 2: LLM 进入 Tool-calling Loop

`BaseAgent.execute()` (`base.py:146-242`) 运行标准的 Agent loop：

```
SystemMessage(prompt) + HumanMessage(state_context)
  → LLM 决定: 调用工具 OR 生成最终决策
  → 如果调用工具: 执行工具 → 追加 ToolResult → 回到 LLM
  → 如果不调用工具: 解析输出为路由决策
```

Orchestrator 可能会先调用 `get_state_summary` 获取详细信息，再调用 `check_answer_quality` 检查某个答案，最后调用 `adjust_difficulty` 调整难度，**然后**才做路由决策。

### Step 3: 解析路由决策

`orchestrator.py:93-134` 解析 LLM 输出的 JSON：

```json
{
  "next_action": "resume_analysis | question_generation | wait_for_answer | answer_analysis | report_generation | end",
  "phase": "当前面试阶段",
  "reasoning": "做出此决策的详细原因",
  "params": {
    "follow_up_needed": false,
    "difficulty_adjustment": null
  }
}
```

### Step 4: Graph 执行路由

`workflow.py:125-172` 中的 `_route_orchestrator()` 将决策映射为 LangGraph 的节点名称，路由到对应的 Agent 节点。每个 Agent 执行完后**回到 Orchestrator**（`workflow.py:85-89`），形成闭环。

### 具体决策场景

**场景一：初始状态（`current_phase = "init"`）**
Orchestrator 发现简历未分析 → 决策 `next_action: "resume_analysis"` → Graph 路由到 ResumeAnalyst → 分析完成后回 Orchestrator

**场景二：简历已分析，题目未生成**
Orchestrator 看到 `has_resume_analysis = true`，`questions_generated = 0` → 决策 `next_action: "generate_questions"` → Graph 路由到 QuestionCurator

**场景三：回答质量不佳（`check_answer_quality` 评分 < 60）**
Orchestrator 调用 `check_answer_quality` 工具 → 发现 `overall_score < 40` → 工具返回 `suggestion: "follow_up_deep_dive"` → Orchestrator 决策生成追问 → `params.follow_up_needed = true` → OrchestratorNode 将追问写入 `pending_follow_ups`

**场景四：难度自适应**
Orchestrator 调用 `check_answer_quality` 发现连续 3 题 > 80 → 调用 `adjust_difficulty("hard")` → 后续题目难度提升

---

## 三、多层降级与故障恢复机制

这是架构中最值得关注的设计。降级不是靠一两处 try-catch，而是形成了一个**分层防护网**：

### 第 1 层：Orchestrator 自身的异常保护

`orchestrator_node.py:64-67`:

```python
except Exception as e:
    logger.error(f"Orchestrator agent failed: {e}", exc_info=True)
    # Graceful degradation: fall back to linear routing
    return _linear_routing(state)
```

当整个 Orchestrator Agent 崩溃时（LLM 不可达、超时等），系统退回到 `_linear_routing()` — 按 `current_phase` 走固定的线性流程，保证面试不中断。

### 第 2 层：路由决策的 Fallback

`workflow.py:150-172` 中，即使 Orchestrator 返回了结果，如果 `next_action` 无法映射到有效节点，会基于 `current_phase` 做二次 Fallback：

```python
# 如果 action 无法映射
fallback_map = {
    "init": "resume_analysis",
    "resume_upload": "resume_analysis",
    "resume_analysis": "resume_analysis",
    "question_generation": "generate_questions",
    "answering": "process_answer",
    "answer_analysis": "analyze_answer",
    "report_generation": "generate_report",
    "completed": "end",
}
```

### 第 3 层：单个 Agent 输出解析失败 → 结构化降级

这是最精细的一层。每个 Agent 的 `parse_output()` 都有明确的失败处理：

**ResumeAnalyst** (`resume_analyst.py:116-123`):
```python
if "error" in analysis:
    return {
        "resume_analyses": [],
        "errors": [{"phase": "resume_analysis", "error_message": ...}],
    }
```
返回空列表 + 错误记录，不阻塞流程。

**QuestionCurator** (`question_curator.py:161-171`):
```python
if not isinstance(questions, list):
    return {
        "questions": [],
        "errors": [{"phase": "question_generation", "error_message": "Agent did not produce a valid question list"}],
    }
```

**AnswerEvaluator — 最复杂的降级** (`answer_evaluator.py:171-177` + `267-353`):

先尝试标准 JSON 解析 → 失败后进入 `_best_effort_parse()`，用**多层正则**从各种格式中提取评分：
- 正则提取 `overall_score`：匹配 `"综合评分：80"`、`**综合评分**: 5/100`、`"overall_score": 85`
- 正则提取各维度分数：匹配 JSON 嵌套对象、Markdown 表格、`key=value` 三种格式
- 正则提取列表（strengths/weaknesses）：匹配 JSON 数组、编号列表、短横线列表
- `authenticity_flag`：在原文中搜索 `consistent`/`inconsistent` 关键词

```python
# 四种 overall_score 提取模式，按优先级
pats = [
    r'(?:\*{0,2})综合评分(?:\*{0,2})\s*[：:]\s*(\d+(?:\.\d+)?)\s*/\s*100',
    r'(?:\*{0,2})综合评分(?:\*{0,2})\s*[：:]\s*(\d+(?:\.\d+)?)',
    r'overall_score\s*[：:]\s*(\d+(?:\.\d+)?)',
    r'"overall_score"\s*:\s*(\d+(?:\.\d+)?)',
]
```

这意味着即使 LLM 输出了 Markdown 表格、中文键名、或 JSON 嵌在文字中间，系统都能提取出评分。

**ReportSynthesizer** (`report_synthesizer.py:172-179`):
解析失败 → 记录错误，且 `hiring_recommendation` 会做合法性检查，非法值统一回退为 `"consider"`。

### 第 4 层：BaseAgent 工具调用失败

`base.py:258-273`:

```python
except Exception as e:
    logger.error(f"[{self.name}] Tool '{tool_name}' failed: {e}", exc_info=True)
    return f"Error executing {tool_name}: {str(e)}"
```

工具执行失败时，**不抛异常**，而是将错误信息作为 `ToolMessage` 返回给 LLM。LLM 看到工具返回了错误信息，可以自主决定重试、换工具、或者继续生成最终输出。这符合 Tool-calling 的标准错误处理模式。

### 第 5 层：达到 max_iterations 上限

`base.py:224-242`:

```python
# Max iterations reached — do one final call to force JSON output
logger.warning(f"[{self.name}] Reached max_iterations...")
try:
    final_response = await self.llm.ainvoke(messages)  # no tools, force text
    ...
except Exception:
    final_content = "{}"
```

当 Agent 在工具调用循环中迭代了 max_iterations 次还没给出最终结果时，系统**强制用不带工具的 LLM 调用**要求生成纯文本输出。如果连这一步都失败了，就返回空 JSON `{}`，由上游的 parse_output 去生成对应的错误记录。

### 第 6 层：Structured Output 的三重解析策略

`structured_output.py` 对 LLM 输出的 JSON 解析有三重保障：
1. **直接解析** — 标准 JSON
2. **截断数组恢复** — LLM 输出被 max_tokens 切断时，逐字符扫描找到所有完整的 `{}` 对象
3. **截断对象恢复** — 计算未闭合的括号深度，补全后解析；如果还失败，回溯到最后一个完整字段

### 第 7 层：Multi-Agent 整体 Fallback 到 Single-Agent

`resumes.py:382-419`:

```python
async def _multi_agent_resume_analysis(ocr_text, resume, settings):
    # ... Multi-agent execution ...
    if analyses:
        return analysis, tokens_used, elapsed_ms

    # Multi-agent produced no valid output → fall back to single-agent pipeline
    logger.warning("ResumeAnalystAgent produced no analysis, falling back to single-agent mode")
    return await _single_agent_resume_analysis(ocr_text, settings)
```

当 Multi-Agent 模式的 ResumeAnalyst 没有产生任何有效分析时，系统**自动回退到原始的 Prompt Template 管线**。这是最终的保险——旧的单 Agent 流程本身就是 Multi-Agent 的降级路径。

### 第 8 层：致命错误终止保护

`routing_node.py:56-59`:

```python
critical_errors = [e for e in errors if e.get("phase") == "answer_analysis"]
if len(critical_errors) >= 3:
    logger.warning(f"Too many errors ({len(critical_errors)}), ending interview")
    return "end"
```

同一阶段连续 3 次以上致命错误，系统判定无法恢复，优雅终止面试。

---

## 降级链路总结

```
Orchestrator 崩溃
  → _linear_routing() 线性回退

Orchestrator 决策无效
  → phase-based fallback_map

单个 Agent 输出解析失败
  → 空结果 + error 记录（不阻塞流程）

AnswerEvaluator JSON 解析失败
  → _best_effort_parse() 正则提取（4种模式 × 3种格式）

工具调用失败
  → 错误信息作为 ToolMessage 反馈给 LLM

达到 max_iterations
  → 强制无工具 LLM 调用 → 还失败就 {}

Multi-Agent 无有效输出
  → 回退到 Single-Agent Pipeline

同阶段致命错误 ≥ 3
  → 优雅终止面试（route to END）
```

这套设计确保了系统的韧性：任何单点故障都不会导致整个面试流程崩溃，而是在该层被捕获并降级到更保守但更可靠的路径上继续运行。
