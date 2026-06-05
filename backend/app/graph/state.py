"""LangGraph InterviewState definition with reducer-based incremental updates."""

import operator
from typing import Annotated, Literal, Optional, TypedDict


class ResumeOCRData(TypedDict):
    resume_id: str
    file_name: str
    raw_text: str
    parsed: dict  # Structured resume info


class ResumeAnalysisOutput(TypedDict):
    resume_id: str
    overall_assessment: str
    strengths: list[str]
    weaknesses: list[str]
    skill_match: dict[str, int]
    experience_relevance_score: int
    project_highlights: list[dict]
    suggested_questions: list[str]
    red_flags: list[str]
    tokens_used: int
    processing_ms: int


class GeneratedQuestion(TypedDict):
    question_id: str
    source_type: Literal["resume_experience", "resume_project", "knowledge_base"]
    source_kb_item_id: Optional[str]
    source_resume_context: Optional[str]
    question_text: str
    ai_reference_answer: Optional[str]
    question_order: int


class AnswerData(TypedDict):
    question_id: str
    transcript_text: str
    audio_minio_key: Optional[str]
    audio_duration_sec: Optional[int]


class AnswerAnalysisOutput(TypedDict, total=False):
    answer_id: str
    question_id: str
    eval_mode: Literal["rag_hybrid", "llm_judge"]

    # LLM-as-a-Judge fields (resume questions)
    accuracy_score: int
    accuracy_reasoning: str
    completeness_score: int
    completeness_reasoning: str
    clarity_score: int
    clarity_reasoning: str
    technical_depth_score: int
    technical_depth_reasoning: str
    overall_score: float

    # RAG hybrid fields (knowledge base questions)
    vector_similarity: float
    retrieved_chunks: list[dict]
    covered_points: list[str]
    missing_points: list[str]

    # Common fields
    assessment: str
    strengths: list[str]
    areas_for_improvement: list[str]
    authenticity_flag: Optional[str]
    tokens_used: int
    processing_ms: int


class InterviewReportOutput(TypedDict):
    session_id: str
    overall_score: float
    dimension_scores: dict[str, float]
    question_reviews: list[dict]
    strengths: list[str]
    weaknesses: list[str]
    hiring_recommendation: Literal[
        "strongly_recommend", "recommend", "consider", "not_recommend"
    ]
    detailed_feedback: str
    tokens_used: int
    processing_ms: int


class AgentTraceData(TypedDict):
    """Per-agent execution trace for audit and debugging."""
    agent: str
    decisions: list[str]
    tool_calls_made: list[str]
    iterations: int
    tokens_used: int
    processing_ms: int


class InterviewState(TypedDict):
    """Full interview workflow state persisted via LangGraph checkpointer.

    List fields use operator.add reducer for incremental appends.
    Each agent outputs structured JSON, not long text — the report agent
    reads summaries, not raw transcripts.

    Multi-agent fields (orchestrator_decision, agent_traces, etc.) are
    optional for backward compatibility with existing checkpoints.
    """

    # Session identifiers
    session_id: str
    thread_id: str
    candidate_id: str
    resume_id: str

    # Workflow control
    current_phase: Literal[
        "init", "resume_upload", "resume_analysis",
        "question_generation", "answering", "answer_analysis",
        "report_generation", "completed"
    ]
    question_source: Literal["resume", "knowledge_base", "mixed"]
    question_index: int
    total_questions: int

    # Data payloads — use operator.add reducer for append-only semantics
    resume_ocr: Optional[ResumeOCRData]
    resume_analyses: Annotated[list[ResumeAnalysisOutput], operator.add]
    questions: Annotated[list[GeneratedQuestion], operator.add]
    answers: Annotated[list[AnswerData], operator.add]
    answer_analyses: Annotated[list[AnswerAnalysisOutput], operator.add]
    interview_report: Optional[InterviewReportOutput]

    # Error tracking
    errors: Annotated[list[dict], operator.add]

    # Timestamps
    started_at: str
    completed_at: Optional[str]

    # ---- Multi-Agent fields (backward compatible — all optional) ----
    orchestrator_decision: Optional[dict]       # Latest routing decision from orchestrator
    agent_traces: Annotated[list[AgentTraceData], operator.add]  # Per-agent execution audit trail
    pending_follow_ups: Annotated[list[dict], operator.add]      # Dynamically generated follow-up Qs
    interview_difficulty: str                   # Dynamic difficulty: "easy" | "medium" | "hard"
    kb_retrieval_cache: Optional[dict]          # Cache for agentic RAG results per question
    resilience_context: Optional[dict]          # Error recovery state for graceful degradation
    kb_configs: Optional[list]                  # KB category distribution configs
    pool_ids: Optional[list]                    # Must-include KB item IDs (question pool)
