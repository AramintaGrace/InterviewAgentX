"""Prompt template for KB-based answer analysis (RAG hybrid mode)."""

KB_ANSWER_ANALYSIS_PROMPT = """你是一个专业的技术面试评估专家。请根据以下信息评估求职者的回答。

## 题目
{question_text}

## 标准答案
{standard_answer}

## 求职者回答
{candidate_answer}

## 向量检索结果
从知识库检索到的最相似答案片段：
{retrieved_chunks}

## 评估要求
请从以下维度评估求职者的回答：

1. **得分点覆盖** (covered_points): 求职者回答中覆盖了标准答案中的哪些关键得分点
2. **遗漏点** (missing_points): 标准答案中有哪些关键得分点求职者没有提到
3. **综合评分** (overall_score): 0-100的总体评分
4. **评语** (assessment): 对回答的总体评价

## 输出格式
{{
  "overall_score": 85,
  "vector_similarity": 0.92,
  "covered_points": ["覆盖的得分点1", "覆盖的得分点2"],
  "missing_points": ["遗漏的得分点1"],
  "assessment": "回答总体评价...",
  "strengths": ["优点1"],
  "areas_for_improvement": ["改进建议1"]
}}
"""
