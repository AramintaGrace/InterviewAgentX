-- ============================================================
-- InterviewAgentX - Initial Database Schema
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- 1. candidates
-- ============================================================
CREATE TABLE IF NOT EXISTS candidates (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(255),
    phone           VARCHAR(30),
    current_role    VARCHAR(200),
    years_of_exp    SMALLINT,
    notes           TEXT,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_candidates_name ON candidates USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email) WHERE is_deleted = FALSE;

-- ============================================================
-- 2. resumes
-- ============================================================
CREATE TABLE IF NOT EXISTS resumes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id    UUID REFERENCES candidates(id) ON DELETE SET NULL,
    file_name       VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    mime_type       VARCHAR(100) NOT NULL DEFAULT 'application/pdf',
    minio_bucket    VARCHAR(200) NOT NULL DEFAULT 'resumes',
    minio_object_key VARCHAR(500) NOT NULL,
    ocr_raw_text    TEXT,
    ocr_status      VARCHAR(30) NOT NULL DEFAULT 'pending',
    ocr_error_msg   TEXT,
    parsed_data     JSONB,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_resumes_candidate ON resumes(candidate_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_resumes_ocr_status ON resumes(ocr_status);

-- ============================================================
-- 3. resume_analyses
-- ============================================================
CREATE TABLE IF NOT EXISTS resume_analyses (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resume_id       UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    agent_model     VARCHAR(100) NOT NULL DEFAULT 'deepseek-chat',
    analysis_json   JSONB NOT NULL,
    tokens_used     INT,
    processing_ms   INT,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_resume_analyses_resume ON resume_analyses(resume_id);

-- ============================================================
-- 4. kb_categories
-- ============================================================
CREATE TABLE IF NOT EXISTS kb_categories (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id       UUID REFERENCES kb_categories(id) ON DELETE SET NULL,
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    sort_order      INT NOT NULL DEFAULT 0,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kb_categories_parent ON kb_categories(parent_id) WHERE is_deleted = FALSE;

-- ============================================================
-- 5. kb_items
-- ============================================================
CREATE TABLE IF NOT EXISTS kb_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id     UUID REFERENCES kb_categories(id) ON DELETE SET NULL,
    question        TEXT NOT NULL,
    answer          TEXT NOT NULL,
    tags            TEXT[] DEFAULT '{}',
    difficulty      VARCHAR(20) DEFAULT 'medium',
    embedding_model VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-small',
    embedding_dim   SMALLINT NOT NULL DEFAULT 1536,
    is_vectorized   BOOLEAN NOT NULL DEFAULT FALSE,
    version         INT NOT NULL DEFAULT 1,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kb_items_category ON kb_items(category_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_kb_items_tags ON kb_items USING gin (tags);
CREATE INDEX IF NOT EXISTS idx_kb_items_question_gin ON kb_items USING gin (question gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_kb_items_deleted ON kb_items(is_deleted);

-- ============================================================
-- 6. interview_sessions
-- ============================================================
CREATE TABLE IF NOT EXISTS interview_sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id    UUID REFERENCES candidates(id) ON DELETE SET NULL,
    resume_id       UUID REFERENCES resumes(id) ON DELETE SET NULL,
    langgraph_thread_id VARCHAR(200) NOT NULL UNIQUE,
    status          VARCHAR(30) NOT NULL DEFAULT 'created',
    question_source VARCHAR(30),
    total_questions SMALLINT NOT NULL DEFAULT 0,
    completed_questions SMALLINT NOT NULL DEFAULT 0,
    total_score     DECIMAL(5,2),
    started_at      TIMESTAMPTZ,
    ended_at        TIMESTAMPTZ,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_interview_sessions_candidate ON interview_sessions(candidate_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_status ON interview_sessions(status);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_thread ON interview_sessions(langgraph_thread_id);

-- ============================================================
-- 7. questions
-- ============================================================
CREATE TABLE IF NOT EXISTS questions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interview_session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    source_type         VARCHAR(20) NOT NULL,
    source_kb_item_id   UUID REFERENCES kb_items(id) ON DELETE SET NULL,
    source_resume_context TEXT,
    question_text       TEXT NOT NULL,
    ai_reference_answer TEXT,
    question_order      SMALLINT NOT NULL DEFAULT 0,
    status              VARCHAR(20) NOT NULL DEFAULT 'pending',
    is_deleted          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_questions_session ON questions(interview_session_id);

-- ============================================================
-- 8. answers
-- ============================================================
CREATE TABLE IF NOT EXISTS answers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id     UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    audio_minio_key VARCHAR(500),
    audio_duration_sec INT,
    transcript_text TEXT NOT NULL,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_answers_question ON answers(question_id);

-- ============================================================
-- 9. answer_analyses
-- ============================================================
CREATE TABLE IF NOT EXISTS answer_analyses (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    answer_id       UUID NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
    question_id     UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    eval_mode       VARCHAR(30) NOT NULL,
    analysis_json   JSONB NOT NULL,
    agent_model     VARCHAR(100) NOT NULL DEFAULT 'deepseek-chat',
    tokens_used     INT,
    processing_ms   INT,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_answer_analyses_answer ON answer_analyses(answer_id);
CREATE INDEX IF NOT EXISTS idx_answer_analyses_question ON answer_analyses(question_id);

-- ============================================================
-- 10. interview_reports
-- ============================================================
CREATE TABLE IF NOT EXISTS interview_reports (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interview_session_id UUID NOT NULL UNIQUE REFERENCES interview_sessions(id) ON DELETE CASCADE,
    report_json         JSONB NOT NULL,
    agent_model         VARCHAR(100) NOT NULL DEFAULT 'deepseek-chat',
    tokens_used         INT,
    processing_ms       INT,
    is_deleted          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_interview_reports_session ON interview_reports(interview_session_id);

-- ============================================================
-- Auto-update updated_at trigger
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN
        SELECT table_name FROM information_schema.columns
        WHERE column_name = 'updated_at' AND table_schema = 'public'
    LOOP
        EXECUTE format('
            CREATE TRIGGER trg_%s_updated_at
            BEFORE UPDATE ON %I
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()',
            t, t);
    END LOOP;
END $$;
