"""OCR service — 硅基流动 deepseek-ai/DeepSeek-OCR.

通过 Chat Completions 多模态接口传入文件（图片/PDF 页），
模型返回 Markdown 格式的文字识别结果。
"""

import base64
import logging
from typing import Optional

import httpx

from app.config import Settings
from app.utils.exceptions import OCRException
from app.utils.proxy import create_http_client

logger = logging.getLogger(__name__)


class OcrService:
    """OCR 文字识别服务，使用硅基流动 DeepSeek-OCR 模型。"""

    _SUPPORTED_MIME_TYPES = {
        "image/png", "image/jpeg", "image/jpg", "image/webp",
        "image/gif", "image/bmp", "image/tiff",
        "application/pdf",
    }

    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.ocr_api_key
        self.base_url = settings.ocr_base_url.rstrip("/")
        self.model = settings.ocr_model

    @property
    def endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    async def extract_text(self, file_data: bytes, file_name: str) -> str:
        """从文件提取文字。

        Args:
            file_data: 原始文件字节。
            file_name: 文件名（用于推断 MIME 类型）。

        Returns:
            提取的 Markdown 文本。
        """
        mime_type = self._guess_mime_type(file_name)

        try:
            client = await create_http_client(timeout_seconds=120.0)
            try:
                data_url = self._encode_data_url(file_data, mime_type)

                body = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": data_url},
                                },
                                {
                                    "type": "text",
                                    "text": "请识别并提取图片中的所有文字内容，保持原始排版格式，输出为Markdown格式。",
                                },
                            ],
                        }
                    ],
                    "max_tokens": 4096,
                    "temperature": 0,
                }

                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }

                response = await client.post(
                    self.endpoint,
                    json=body,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()
                text = result["choices"][0]["message"]["content"]
                logger.info(f"OCR extracted {len(text)} characters from {file_name}")
                return text

            finally:
                await client.aclose()

        except httpx.HTTPStatusError as e:
            logger.error(f"OCR API HTTP {e.response.status_code}: {e.response.text}")
            raise OCRException(f"OCR API error ({e.response.status_code})")
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            raise OCRException(f"OCR failed: {e}")

    def _encode_data_url(self, file_data: bytes, mime_type: str) -> str:
        """将文件字节编码为 data URL，供多模态 API 使用。"""
        b64 = base64.b64encode(file_data).decode("ascii")
        return f"data:{mime_type};base64,{b64}"

    @staticmethod
    def _guess_mime_type(file_name: str) -> str:
        """根据文件扩展名推断 MIME 类型。"""
        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        mapping = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "webp": "image/webp",
            "gif": "image/gif",
            "bmp": "image/bmp",
            "tiff": "image/tiff",
            "tif": "image/tiff",
            "pdf": "application/pdf",
        }
        return mapping.get(ext, "application/octet-stream")

    async def parse_resume_info(self, ocr_text: str) -> dict:
        """从 OCR 文本中提取结构化简历信息（复用 DeepSeek Chat）。"""
        if not ocr_text.strip():
            return {}

        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=self.settings.deepseek_model_chat,
            api_key=self.settings.deepseek_api_key,
            base_url=self.settings.deepseek_base_url,
            temperature=0,
        )

        prompt = f"""Extract structured information from the following resume text.
Return ONLY valid JSON with these fields:
- name: string or null
- email: string or null
- phone: string or null
- education: array of {{school, degree, year}}
- experience: array of {{company, role, duration, description}}
- skills: array of strings
- projects: array of {{name, description, tech_stack}}

Resume text:
{ocr_text[:8000]}

JSON output:"""

        try:
            response = await llm.ainvoke(prompt)
            import json
            content = response.content if hasattr(response, "content") else str(response)
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to parse resume info: {e}")
            return {}
