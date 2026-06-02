"""Speech-to-Text (STT) service — 硅基流动 FunAudioLLM/SenseVoiceSmall."""

import logging
from typing import AsyncGenerator, Optional

import httpx

from app.config import Settings
from app.utils.exceptions import STTException
from app.utils.proxy import create_http_client

logger = logging.getLogger(__name__)


class STTService:
    """Service for real-time speech-to-text conversion.

    使用硅基流动 FunAudioLLM/SenseVoiceSmall 模型进行语音转文本。
    API格式完全兼容 OpenAI /v1/audio/transcriptions。
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.stt_api_key
        self.base_url = settings.stt_base_url
        self.model = settings.stt_model

    @property
    def endpoint(self) -> str:
        """完整的语音转文本 API 端点."""
        return f"{self.base_url.rstrip('/')}/audio/transcriptions"

    async def transcribe_file(self, audio_data: bytes, format: str = "webm") -> str:
        """Transcribe a complete audio file (non-streaming)."""
        try:
            client = await create_http_client(timeout_seconds=60.0)
            try:
                files = {"file": (f"audio.{format}", audio_data, f"audio/{format}")}
                data = {"model": self.model}
                headers = {"Authorization": f"Bearer {self.api_key}"}

                response = await client.post(
                    self.endpoint,
                    files=files,
                    data=data,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("text", "")

            finally:
                await client.aclose()
        except httpx.HTTPStatusError as e:
            logger.error(f"STT API HTTP {e.response.status_code}: {e.response.text}")
            raise STTException(f"Speech-to-text API error ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            logger.error(f"STT transcription failed: {e}")
            raise STTException(f"Speech-to-text failed: {e}")

    async def transcribe_stream(
        self,
        audio_chunks: AsyncGenerator[bytes, None],
        format: str = "webm",
    ) -> AsyncGenerator[str, None]:
        """Stream audio chunks and yield partial/final transcriptions.

        This is the core method used by the WebSocket endpoint.
        Yields JSON-serializable dicts with type and text fields.
        """
        # Accumulate audio chunks for processing
        buffer = b""
        async for chunk in audio_chunks:
            buffer += chunk
            # 每累积约 1 秒的音频（16kHz 采样率）发送一次部分转录
            if len(buffer) > 16000:
                try:
                    partial = await self.transcribe_file(buffer, format)
                    yield f'{{"type": "partial", "text": "{partial}"}}'
                except Exception:
                    pass
                buffer = b""

        # Final transcription
        if buffer:
            try:
                final_text = await self.transcribe_file(buffer, format)
                yield f'{{"type": "final", "text": "{final_text}"}}'
            except Exception as e:
                yield f'{{"type": "error", "message": "{str(e)}"}}'

        yield '{"type": "end"}'
