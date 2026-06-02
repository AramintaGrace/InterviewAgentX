"""Custom exception classes for InterviewAgentX."""


class InterviewAgentXException(Exception):
    """Base exception for the application."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class NotFoundException(InterviewAgentXException):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code="NOT_FOUND")


class OCRException(InterviewAgentXException):
    """OCR processing error."""

    def __init__(self, message: str = "OCR processing failed"):
        super().__init__(message, code="OCR_ERROR")


class STTException(InterviewAgentXException):
    """Speech-to-text processing error."""

    def __init__(self, message: str = "Speech-to-text failed"):
        super().__init__(message, code="STT_ERROR")


class MilvusException(InterviewAgentXException):
    """Milvus vector database error."""

    def __init__(self, message: str = "Vector database operation failed"):
        super().__init__(message, code="MILVUS_ERROR")


class MinIOException(InterviewAgentXException):
    """MinIO storage error."""

    def __init__(self, message: str = "File storage operation failed"):
        super().__init__(message, code="MINIO_ERROR")


class AgentException(InterviewAgentXException):
    """AI Agent execution error."""

    def __init__(self, message: str = "Agent execution failed"):
        super().__init__(message, code="AGENT_ERROR")


class KnowledgeBaseException(InterviewAgentXException):
    """Knowledge base operation error."""

    def __init__(self, message: str = "Knowledge base operation failed"):
        super().__init__(message, code="KB_ERROR")
