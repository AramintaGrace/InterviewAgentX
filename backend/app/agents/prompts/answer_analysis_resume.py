"""Prompt template for resume-based answer analysis (LLM-as-a-Judge mode)."""

LLM_JUDGE_PROMPT = """你是一个专业的技术面试评估专家。请对求职者的回答进行评估。

## 规则（必须遵守）
- 只输出纯JSON，不要Markdown标记、表格、粗体或任何其他格式
- 不要在JSON前后添加任何解释文字
- 直接输出以{开头、以}结尾的JSON对象

## 候选人简历相关片段
{resume_context}

## 面试题目
{question_text}

## AI参考答案（仅供参考，非标准答案）
{ai_reference_answer}

## 求职者实际回答
{candidate_answer}

## 评估维度
从以下四个维度评分，每个维度独立给出1-5分和推理：
1. accuracy（真实性）：回答是否与简历一致？技术细节是否合理可信？
2. completeness（完整性）：是否全面回答了问题？
3. clarity（表达清晰度）：结构是否清晰？语言是否流畅？
4. technical_depth（技术深度）：是否展示了足够的技术深度和实现细节？

综合评分 overall_score(0-100)，authenticity_flag取 consistent/inconsistent/uncertain。

## 输出格式
{{"accuracy":{{"score":4,"reasoning":"..."}},"completeness":{{"score":3,"reasoning":"..."}},"clarity":{{"score":5,"reasoning":"..."}},"technical_depth":{{"score":4,"reasoning":"..."}},"overall_score":80.0,"assessment":"综合评语","strengths":["优点"],"areas_for_improvement":["改进点"],"authenticity_flag":"consistent"}}
"""
