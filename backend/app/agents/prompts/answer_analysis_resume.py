"""Prompt template for resume-based answer analysis (LLM-as-a-Judge mode)."""

LLM_JUDGE_PROMPT = """你是一个专业的技术面试评估专家。请对求职者的回答进行多维度评估。

## 候选人简历相关片段
{resume_context}

## 面试题目
{question_text}

## AI参考答案（仅供参考，非标准答案）
{ai_reference_answer}

## 求职者实际回答
{candidate_answer}

## 评估模式：LLM-as-a-Judge
由于这是基于简历经历的开放性问题，没有标准答案。请从以下四个维度评估：

### 1. 真实性 (accuracy)
- 求职者的回答是否与其简历中描述的经历一致？
- 回答中的技术细节是否合理可信？
- 评分：1-5

### 2. 完整性 (completeness)
- 是否全面回答了问题的各个方面？
- 是否使用了STAR法则（情境-任务-行动-结果）？
- 评分：1-5

### 3. 表达清晰度 (clarity)
- 回答结构是否清晰？
- 语言表达是否流畅？
- 评分：1-5

### 4. 技术深度 (technical_depth)
- 是否展示了足够的技术理解深度？
- 是否有具体的实现细节和思考过程？
- 评分：1-5

### 5. 综合评分
- overall_score: 0-100的综合评分（不是简单的维度平均）

### 6. 真实性标记
- authenticity_flag: "consistent"（与简历一致）、"inconsistent"（存在矛盾）或 "uncertain"（无法判断）

## 输出格式
{{
  "accuracy": {{"score": 4, "reasoning": "..."}},
  "completeness": {{"score": 3, "reasoning": "..."}},
  "clarity": {{"score": 5, "reasoning": "..."}},
  "technical_depth": {{"score": 4, "reasoning": "..."}},
  "overall_score": 80.0,
  "assessment": "综合评语...",
  "strengths": ["优点1", "优点2"],
  "areas_for_improvement": ["改进点1"],
  "authenticity_flag": "consistent"
}}
"""
