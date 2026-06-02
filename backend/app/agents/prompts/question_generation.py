"""Prompt templates for the Question Generation Agent."""

RESUME_QUESTION_PROMPT = """你是一个专业的面试官。请根据以下候选人简历信息生成面试题目。

## 候选人简历信息
{resume_context}

## 简历分析结果
{resume_analysis}

## 要求
基于简历中的工作经历和项目经历，生成 {count} 道面试题目。题目应：
- 深入考察候选人的技术能力和项目经验
- 包含行为面试题（STAR方法）
- 包含技术深挖题
- 难度递进

请返回JSON数组：
[
  {{
    "source_type": "resume_experience 或 resume_project",
    "source_resume_context": "简历中相关的经历/项目片段",
    "question_text": "完整的面试问题",
    "ai_reference_answer": "对于这个问题的理想答案要点"
  }}
]
"""

KB_QUESTION_PROMPT = """你是一个专业的面试官。请根据以下知识库条目生成面试题目。

## 知识库条目
{knowledge_base_items}

## 要求
从以上知识库中选择 {count} 道合适的面试题目（直接使用知识库中的问题和答案），并按以下JSON格式返回：

[
  {{
    "source_type": "knowledge_base",
    "source_kb_item_id": "知识库条目的UUID",
    "question_text": "面试问题（与知识库一致）",
    "ai_reference_answer": null
  }}
]

注意：source_kb_item_id 必须与提供的知识库条目ID完全匹配。
"""

MIXED_QUESTION_PROMPT = """你是一个专业的面试官。请根据以下信息混合生成面试题目。

## 候选人简历信息
{resume_context}

## 简历分析结果
{resume_analysis}

## 知识库条目
{knowledge_base_items}

## 要求
共生成 {count} 道题目，要求：
- 约60%的题目来自简历经历和项目
- 约40%的题目来自知识库
- 题目难度递进

返回JSON数组，每个题目需要标注source_type。
"""
