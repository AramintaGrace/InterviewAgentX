"""Prompt templates for Agentic RAG retrieval decisions.

These prompts enable the 7-step agentic retrieval loop:
  1. DECIDE:      Should I retrieve for this query?
  2. FORMULATE:   Generate optimal search query
  3. EXECUTE:     Multi-strategy search (handled by AgenticRetriever class)
  4. EVALUATE:    Are retrieved documents relevant?
  5. RE-RETRIEVE: If quality low, reformulate and retry
  6. SYNTHESIZE:  Use retrieved context + LLM reasoning
  7. CITE:        Reference which KB items were used
"""

# ---- Step 1-2: Decide whether to retrieve and formulate query ----

QUERY_FORMULATION_PROMPT = """你是一个智能检索决策助手。根据上下文和原始查询，判断是否需要从外部知识库检索，并生成最优检索查询。

## 当前上下文（为什么需要检索）
{context}

## 原始查询
{original_query}

## 任务
1. 判断是否需要检索知识库（如果问题可直接从上下文回答，则不需要）
2. 如果需要检索，生成最优检索查询词（可能与原始查询不同）：
   - 提取核心技术术语
   - 去除对话性语言
   - 添加相关同义词
   - 保持简洁（最多15个词）
3. 如果不需要检索，说明原因

请严格返回JSON：
{{"should_retrieve": true/false, "search_query": "优化后的检索查询", "reasoning": "决策原因"}}
"""

# ---- Step 4: Evaluate relevance of retrieved documents ----

RELEVANCE_JUDGMENT_PROMPT = """你是一个检索相关性评估助手。评估检索到的文档与原始查询的相关性。

## 原始查询
{query}

## 检索到的文档
{documents}

## 任务
对每个文档评估其与查询的相关性，分数 0.0（完全无关）到 1.0（高度相关）。
评估标准：
- 文档内容是否直接回答查询
- 文档中的技术概念是否与查询匹配
- 文档是否提供了有用的上下文信息

请严格返回JSON：
{{"scores": [0.95, 0.7, ...], "overall_relevance": 0.85, "explanation": "总体相关性评估说明"}}
"""

# ---- Step 6-7: Synthesize relevance summary with citations ----

RESULT_SYNTHESIS_PROMPT = """你是一个检索结果综合助手。总结检索到的文档如何帮助回答查询。

## 查询
{query}

## 检索到的文档
{documents}

## 任务
用2-3句话总结这些文档与查询的相关性，包括：
- 哪些文档最相关，为什么
- 文档中的关键知识点
- 是否充分覆盖了查询涉及的技术领域

请直接返回简短的总结文本（不需要JSON格式）。
"""
