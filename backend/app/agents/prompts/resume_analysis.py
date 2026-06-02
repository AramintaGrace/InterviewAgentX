"""Prompt template for the Resume Analysis Agent."""

RESUME_ANALYSIS_PROMPT = """你是一个专业的简历分析专家。请根据以下简历信息进行全面分析。

## 简历信息
{resume_text}

## 分析要求
请从以下维度进行分析，并返回结构化JSON：

1. **综合评估** (overall_assessment): 对候选人整体素质的简要评价
2. **优势** (strengths): 候选人突出的优势，至少3条
3. **不足之处** (weaknesses): 简历中体现的短板或风险点
4. **技能匹配度** (skill_match): 关键技能的掌握程度评分(1-10)
5. **经验相关度** (experience_relevance_score): 整体经验匹配度(1-100)
6. **项目亮点** (project_highlights): 值得深入询问的项目经历
7. **建议面试题目** (suggested_questions): 基于简历提出的面试问题，至少5题
8. **风险提示** (red_flags): 需要面试中特别关注的疑点

## 输出格式
请严格按照以下JSON格式返回（不要包含markdown代码块标记）：

{{
  "overall_assessment": "综合评价...",
  "strengths": ["优势1", "优势2", "优势3"],
  "weaknesses": ["不足1", "不足2"],
  "skill_match": {{"Python": 8, "FastAPI": 7}},
  "experience_relevance_score": 75,
  "project_highlights": [
    {{"project": "项目名称", "depth_analysis": "值得深挖的方向"}}
  ],
  "suggested_questions": [
    "问题1", "问题2", "问题3", "问题4", "问题5"
  ],
  "red_flags": ["需要关注的疑点"]
}}
"""
