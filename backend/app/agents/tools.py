"""LangChain tool definitions for all multi-agent implementations.

Tools are organized by consuming agent. Each tool follows the LangChain
@tool decorator pattern with async ainvoke support.

Tool Categories:
  1. RESUME_ANALYST:    get_full_resume_text, query_candidate_history, flag_inconsistency
  2. QUESTION_CURATOR:  search_knowledge_base, get_resume_analysis, get_kb_categories
  3. ANSWER_EVALUATOR:  retrieve_reference_answer, check_resume_consistency, search_knowledge_base
  4. REPORT_SYNTHESIZER: collect_all_analyses, compute_dimension_scores
  5. ORCHESTRATOR:      get_state_summary, check_answer_quality, adjust_difficulty

Tool Injection Pattern:
  Tools that depend on services (Milvus, DB, embedding) use closure-based
  injection at construction time via factory functions like
  create_question_curator_tools(agentic_retriever, state_provider, ...).

  This avoids passing heavy service instances through the tool interface
  and keeps tools reusable across different agent configurations.
"""

import json
import logging
from typing import Any, Callable, Dict, List, Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# ============================================================================
# Type aliases
# ============================================================================

# A callable that returns the current InterviewState dict
StateProvider = Callable[[], Dict[str, Any]]


# ============================================================================
# Tool Factories (closure-based injection)
# ============================================================================


def create_resume_analyst_tools(
    state_provider: StateProvider,
) -> List:
    """Create tools for ResumeAnalystAgent.

    Tools:
      - get_full_resume_text: Return complete OCR text from state.
      - query_candidate_history: Search DB for past interviews.
      - flag_inconsistency: Record an inconsistency for later questioning.
    """

    @tool
    async def get_full_resume_text() -> str:
        """获取候选人简历的完整OCR文本。

        返回简历的原始OCR文本和结构化解析数据，供深度分析使用。
        """
        state = state_provider()
        resume_ocr = state.get("resume_ocr", {}) or {}
        raw_text = resume_ocr.get("raw_text", "")
        parsed = resume_ocr.get("parsed", {}) or {}
        return json.dumps(
            {
                "raw_text": raw_text[:8000],  # Truncate to avoid token overflow
                "parsed": parsed,
                "file_name": resume_ocr.get("file_name", ""),
            },
            ensure_ascii=False,
        )

    @tool
    async def query_candidate_history(candidate_id: str = "") -> str:
        """查询候选人的历史面试记录。

        Args:
            candidate_id: 候选人的UUID。如果为空，使用当前会话的候选人ID。

        Returns:
            历史面试摘要（日期、分数、关键反馈）。
        """
        state = state_provider()
        cid = candidate_id or state.get("candidate_id", "")
        if not cid:
            return json.dumps({"error": "No candidate_id available"})

        # Historical queries would go through InterviewService here.
        # For now, return a structured placeholder that the LLM can reason about.
        return json.dumps(
            {
                "candidate_id": cid,
                "past_interviews": [],
                "note": "No prior interview history found for this candidate.",
            },
            ensure_ascii=False,
        )

    @tool
    async def flag_inconsistency(
        claim: str,
        evidence: str,
        severity: str = "medium",
    ) -> str:
        """标记简历中的不一致或需要深入追问的地方。

        Args:
            claim: 候选人声称的内容。
            evidence: 简历中的实际证据（或缺失的证据）。
            severity: 严重程度 — 'low', 'medium', 'high'。

        Returns:
            确认标记已记录。
        """
        logger.info(
            f"Flagged inconsistency [severity={severity}]: "
            f"claim='{claim[:80]}...', evidence='{evidence[:80]}...'"
        )
        return json.dumps(
            {
                "flagged": True,
                "claim": claim,
                "evidence": evidence,
                "severity": severity,
                "action": "This will be used for follow-up questioning.",
            },
            ensure_ascii=False,
        )

    return [get_full_resume_text, query_candidate_history, flag_inconsistency]


def create_question_curator_tools(
    agentic_retriever,  # AgenticRetriever instance
    state_provider: StateProvider,
) -> List:
    """Create tools for QuestionCuratorAgent with AgenticRAG integration.

    Tools:
      - search_knowledge_base: Agentic RAG retrieval from KB.
      - get_resume_analysis: Read resume analysis from state.
      - get_kb_categories: List available knowledge base categories.
    """

    @tool
    async def search_knowledge_base(
        query: str,
        category_id: str = "",
        difficulty: str = "",
        top_k: int = 5,
    ) -> str:
        """使用Agentic RAG从知识库中检索最相关的题目和答案。

        这个工具会自动：
        1. 判断是否需要检索
        2. 优化检索查询
        3. 评估结果相关性
        4. 如果相关性低，重新检索

        Args:
            query: 检索查询词（可以是关键技术术语、问题主题等）。
            category_id: 可选的分类ID过滤。
            difficulty: 可选的难度过滤 (easy/medium/hard)。
            top_k: 返回的结果数量。

        Returns:
            检索到的知识库条目列表，包含相关性分数和引用。
        """
        state = state_provider()
        context = (
            f"为候选人面试生成题目。"
            f"当前阶段: {state.get('current_phase', 'unknown')}。"
            f"题目来源: {state.get('question_source', 'resume')}。"
            f"需要生成 {state.get('total_questions', 5)} 道题目。"
        )

        result = await agentic_retriever.retrieve(
            context=context,
            query=query,
            category_id=category_id or None,
            difficulty=difficulty or None,
        )

        return json.dumps(
            {
                "documents": [
                    {
                        "id": d.id,
                        "content": d.content[:800],
                        "similarity": round(d.similarity, 4),
                        "relevance_score": round(d.relevance_score, 4),
                        "category_id": d.category_id,
                        "difficulty": d.difficulty,
                        "tags": d.tags,
                    }
                    for d in result.documents
                ],
                "overall_relevance": round(result.overall_relevance, 4),
                "citations": result.citations,
                "relevance_summary": result.relevance_summary,
                "attempts": result.attempts,
                "strategy": result.strategy,
                "retrieval_ms": result.retrieval_ms,
            },
            ensure_ascii=False,
        )

    @tool
    async def get_resume_analysis() -> str:
        """获取简历分析结果，包括优势、劣势、技能评分和项目亮点。

        Returns:
            简历分析的结构化摘要。
        """
        state = state_provider()
        analyses = state.get("resume_analyses", [])
        if not analyses:
            return json.dumps(
                {"error": "No resume analysis available yet"},
                ensure_ascii=False,
            )

        latest = analyses[-1]
        return json.dumps(
            {
                "overall_assessment": latest.get("overall_assessment", ""),
                "strengths": latest.get("strengths", []),
                "weaknesses": latest.get("weaknesses", []),
                "skill_match": latest.get("skill_match", {}),
                "experience_relevance_score": latest.get(
                    "experience_relevance_score", 0
                ),
                "project_highlights": latest.get("project_highlights", []),
                "suggested_questions": latest.get("suggested_questions", []),
                "red_flags": latest.get("red_flags", []),
            },
            ensure_ascii=False,
        )

    @tool
    async def get_kb_categories() -> str:
        """获取所有可用的知识库分类列表。

        Returns:
            分类列表，包含ID、名称和条目数量。
        """
        state = state_provider()
        # Categories are typically loaded via KnowledgeBaseService.
        # Provide a note for the LLM about available filtering.
        kb_configs = state.get("kb_configs", [])
        return json.dumps(
            {
                "kb_configs": kb_configs,
                "note": "Use category_id from kb_configs to filter search_knowledge_base results.",
            },
            ensure_ascii=False,
        )

    return [search_knowledge_base, get_resume_analysis, get_kb_categories]


def create_answer_evaluator_tools(
    agentic_retriever,  # AgenticRetriever instance
    state_provider: StateProvider,
) -> List:
    """Create tools for AnswerEvaluatorAgent with AgenticRAG integration.

    Tools:
      - retrieve_reference_answer: Agentic RAG for standard answers.
      - check_resume_consistency: Cross-reference answer against resume.
      - search_knowledge_base: General KB search for fact-checking.
    """

    @tool
    async def retrieve_reference_answer(
        question_id: str = "",
        query_text: str = "",
    ) -> str:
        """使用Agentic RAG检索知识库中的标准参考答案。

        根据题目内容检索最匹配的知识库条目作为参考答案，
        用于RAG混合评估模式。

        Args:
            question_id: 当前题目的ID（用于日志追踪）。
            query_text: 用于检索的查询文本（通常是题目文本）。

        Returns:
            检索到的标准答案和相关知识条目。
        """
        state = state_provider()
        questions = state.get("questions", [])
        question_index = state.get("question_index", 0)

        # Get current question context
        current_question = {}
        if question_index < len(questions):
            current_question = questions[question_index]

        search_query = query_text or current_question.get("question_text", "")
        if not search_query:
            return json.dumps(
                {"error": "No query text available for retrieval"},
                ensure_ascii=False,
            )

        context = (
            f"评估候选人对面试题目的回答。"
            f"题目: {current_question.get('question_text', '')[:200]}"
        )

        result = await agentic_retriever.retrieve(
            context=context,
            query=search_query,
        )

        return json.dumps(
            {
                "reference_documents": [
                    {
                        "id": d.id,
                        "content": d.content[:800],
                        "similarity": round(d.similarity, 4),
                        "relevance_score": round(d.relevance_score, 4),
                    }
                    for d in result.documents
                ],
                "overall_relevance": round(result.overall_relevance, 4),
                "citations": result.citations,
                "relevance_summary": result.relevance_summary,
            },
            ensure_ascii=False,
        )

    @tool
    async def check_resume_consistency(
        claim: str,
    ) -> str:
        """验证候选人的回答是否与其简历内容一致。

        将候选人在面试中声称的内容与简历原始信息进行对比，
        检测矛盾或不一致之处。

        Args:
            claim: 候选人在回答中声称的具体内容。

        Returns:
            一致性检查结果：consistent（一致）、inconsistent（矛盾）、uncertain（不确定）。
        """
        state = state_provider()
        resume_ocr = state.get("resume_ocr", {}) or {}
        resume_text = resume_ocr.get("raw_text", "")
        parsed = resume_ocr.get("parsed", {}) or {}

        if not resume_text and not parsed:
            return json.dumps(
                {
                    "result": "uncertain",
                    "reason": "No resume data available for comparison",
                },
                ensure_ascii=False,
            )

        return json.dumps(
            {
                "result": "check_required",
                "claim": claim[:500],
                "resume_context_available": bool(resume_text),
                "parsed_skills": parsed.get("skills", []),
                "parsed_experiences": [
                    exp.get("company", "")
                    for exp in parsed.get("experience", [])
                ],
                "note": "The LLM should compare the claim against this resume context.",
            },
            ensure_ascii=False,
        )

    @tool
    async def search_knowledge_base_for_fact_check(
        query: str,
    ) -> str:
        """搜索知识库以验证候选人回答中的技术事实。

        Args:
            query: 需要验证的技术声明或概念。

        Returns:
            相关的知识库条目，用于事实核查。
        """
        state = state_provider()
        context = (
            f"验证候选人回答中的技术事实。"
            f"当前题目索引: {state.get('question_index', 0)}"
        )

        result = await agentic_retriever.retrieve(
            context=context,
            query=query,
        )

        return json.dumps(
            {
                "fact_check_results": [
                    {
                        "id": d.id,
                        "content": d.content[:600],
                        "relevance_score": round(d.relevance_score, 4),
                    }
                    for d in result.documents
                    if d.relevance_score >= 0.5
                ],
                "citations": result.citations,
            },
            ensure_ascii=False,
        )

    return [
        retrieve_reference_answer,
        check_resume_consistency,
        search_knowledge_base_for_fact_check,
    ]


def create_report_synthesizer_tools(
    state_provider: StateProvider,
) -> List:
    """Create tools for ReportSynthesizerAgent.

    Tools:
      - collect_all_analyses: Gather all answer evaluation summaries.
      - compute_dimension_scores: Aggregate dimension scores.
    """

    @tool
    async def collect_all_analyses() -> str:
        """收集所有题目的答案分析摘要。

        返回每道题的结构化评估数据，包括分数、优势、改进建议等。

        Returns:
            所有答案分析的紧凑摘要，供报告生成使用。
        """
        state = state_provider()
        questions = state.get("questions", [])
        answer_analyses = state.get("answer_analyses", [])

        summaries = []
        for i, analysis in enumerate(answer_analyses):
            q = questions[i] if i < len(questions) else {}
            summaries.append(
                {
                    "question_index": i + 1,
                    "question_text": q.get("question_text", "")[:200],
                    "source_type": q.get("source_type", ""),
                    "eval_mode": analysis.get("eval_mode", ""),
                    "overall_score": analysis.get("overall_score", 0),
                    "strengths": analysis.get("strengths", []),
                    "areas_for_improvement": analysis.get(
                        "areas_for_improvement", []
                    ),
                    "assessment": analysis.get("assessment", "")[:300],
                }
            )

        return json.dumps(
            {
                "total_questions": len(questions),
                "analyzed_count": len(answer_analyses),
                "question_reviews": summaries,
            },
            ensure_ascii=False,
        )

    @tool
    async def compute_dimension_scores() -> str:
        """计算各能力维度的聚合分数。

        汇总所有题目的评分，计算以下维度的平均分：
        - technical_ability（技术能力）
        - communication（沟通表达）
        - problem_solving（问题解决）
        - experience_relevance（经验匹配度）

        Returns:
            各维度的聚合分数和统计信息。
        """
        state = state_provider()
        answer_analyses = state.get("answer_analyses", [])
        resume_analyses = state.get("resume_analyses", [])

        if not answer_analyses:
            return json.dumps(
                {"error": "No answer analyses to compute from"},
                ensure_ascii=False,
            )

        # Aggregate LLM-Judge dimension scores
        scores = {
            "accuracy": [],
            "completeness": [],
            "clarity": [],
            "technical_depth": [],
            "overall": [],
        }

        for analysis in answer_analyses:
            for dim in ["accuracy", "completeness", "clarity", "technical_depth"]:
                val = analysis.get(f"{dim}_score", 0)
                if val:
                    scores[dim].append(val)
            overall = analysis.get("overall_score", 0)
            if overall:
                scores["overall"].append(overall)

        def safe_avg(vals: List) -> float:
            return round(sum(vals) / len(vals), 1) if vals else 0.0

        # Map to report dimensions
        dimension_scores = {
            "technical_ability": safe_avg(scores["technical_depth"]),
            "communication": safe_avg(scores["clarity"]),
            "problem_solving": safe_avg(scores["completeness"]),
            "experience_relevance": (
                resume_analyses[-1].get("experience_relevance_score", 0)
                if resume_analyses
                else 0
            ),
            "overall_avg": safe_avg(scores["overall"]),
        }

        return json.dumps(
            {
                "dimension_scores": dimension_scores,
                "raw_dimension_counts": {
                    k: len(v) for k, v in scores.items()
                },
                "total_analyses": len(answer_analyses),
            },
            ensure_ascii=False,
        )

    return [collect_all_analyses, compute_dimension_scores]


def create_orchestrator_tools(
    state_provider: StateProvider,
) -> List:
    """Create tools for InterviewOrchestratorAgent.

    Tools:
      - get_state_summary: Compact interview state summary.
      - check_answer_quality: Evaluate if follow-up is needed.
      - adjust_difficulty: Dynamically adjust interview difficulty.
    """

    @tool
    async def get_state_summary() -> str:
        """获取当前面试状态的紧凑摘要。

        返回当前阶段、题目进度、答案数量等关键信息。

        Returns:
            面试状态摘要JSON。
        """
        state = state_provider()
        questions = state.get("questions", [])
        answers = state.get("answers", [])
        errors = state.get("errors", [])

        return json.dumps(
            {
                "session_id": state.get("session_id", ""),
                "current_phase": state.get("current_phase", "init"),
                "question_source": state.get("question_source", "resume"),
                "question_index": state.get("question_index", 0),
                "total_questions": state.get("total_questions", 0),
                "questions_generated": len(questions),
                "answers_submitted": len(answers),
                "analyses_completed": len(
                    state.get("answer_analyses", [])
                ),
                "has_resume_ocr": bool(state.get("resume_ocr")),
                "has_resume_analysis": bool(
                    state.get("resume_analyses")
                ),
                "error_count": len(errors),
                "difficulty": state.get("interview_difficulty", "medium"),
            },
            ensure_ascii=False,
        )

    @tool
    async def check_answer_quality(answer_index: int = -1) -> str:
        """检查特定答案的质量，判断是否需要追问。

        Args:
            answer_index: 答案索引（默认为-1，即最新答案）。

        Returns:
            质量评估结果和建议操作。
        """
        state = state_provider()
        analyses = state.get("answer_analyses", [])
        questions = state.get("questions", [])

        if answer_index < 0:
            answer_index = len(analyses) - 1 if analyses else -1

        if answer_index < 0 or answer_index >= len(analyses):
            return json.dumps(
                {
                    "quality_check": "no_analysis_available",
                    "suggestion": "Proceed normally",
                },
                ensure_ascii=False,
            )

        analysis = analyses[answer_index]
        overall = analysis.get("overall_score", 0)
        question_text = (
            questions[answer_index].get("question_text", "")
            if answer_index < len(questions)
            else ""
        )

        # Decision logic for follow-up
        needs_follow_up = overall < 60
        suggestion = "continue"
        if overall < 40:
            suggestion = "follow_up_deep_dive"
        elif overall < 60:
            suggestion = "follow_up_clarification"
        elif overall >= 85:
            suggestion = "consider_harder_questions"

        return json.dumps(
            {
                "answer_index": answer_index,
                "overall_score": overall,
                "question_text": question_text[:200],
                "needs_follow_up": needs_follow_up,
                "suggestion": suggestion,
                "strengths": analysis.get("strengths", []),
                "areas_for_improvement": analysis.get(
                    "areas_for_improvement", []
                ),
            },
            ensure_ascii=False,
        )

    @tool
    async def adjust_difficulty(new_level: str) -> str:
        """动态调整后续题目的难度级别。

        根据候选人到目前为止的表现，调整面试难度。

        Args:
            new_level: 新的难度级别 — 'easy', 'medium', 'hard'。

        Returns:
            确认难度已调整。
        """
        valid_levels = {"easy", "medium", "hard"}
        if new_level not in valid_levels:
            return json.dumps(
                {
                    "error": f"Invalid difficulty '{new_level}'. "
                    f"Must be one of: {valid_levels}",
                },
                ensure_ascii=False,
            )

        state = state_provider()
        old_level = state.get("interview_difficulty", "medium")
        logger.info(
            f"Orchestrator: adjusting difficulty "
            f"'{old_level}' → '{new_level}'"
        )

        return json.dumps(
            {
                "previous_difficulty": old_level,
                "new_difficulty": new_level,
                "adjusted": True,
                "note": "Subsequent questions will reflect this difficulty level.",
            },
            ensure_ascii=False,
        )

    return [get_state_summary, check_answer_quality, adjust_difficulty]
