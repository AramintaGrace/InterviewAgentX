"""OCR service — 硅基流动 deepseek-ai/DeepSeek-OCR via base64.

PDF: pymupdf 逐页渲染为 PNG → base64 → 逐页 OCR → 合并。
Image: 直接 base64 编码 → OCR。
"""

import base64
import logging
import re
from typing import Optional
from io import BytesIO

import httpx

from app.config import Settings
from app.utils.exceptions import OCRException
from app.utils.proxy import create_http_client

logger = logging.getLogger(__name__)


class OcrService:
    """OCR 文字识别服务。"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.ocr_api_key
        self.base_url = settings.ocr_base_url.rstrip("/")
        self.model = settings.ocr_model

    @property
    def endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    async def extract_text(self, file_data: bytes, file_name: str) -> str:
        """从图片/PDF 提取文字。

        - 图片 (PNG/JPG/…): 直接 base64 编码后 OCR
        - PDF: pymupdf 逐页渲染为 PNG → 逐页 base64 OCR → 合并
        """
        mime_type = self._guess_mime_type(file_name)

        if mime_type == "application/pdf":
            return await self._extract_pdf(file_data, file_name)

        # 单张图片：直接 base64 OCR
        return await self._ocr_image(file_data, mime_type)

    async def _extract_pdf(self, file_data: bytes, file_name: str) -> str:
        """PDF: 逐页渲染为 PNG → 逐页 OCR → 合并结果。"""
        try:
            import fitz  # pymupdf
        except ImportError:
            raise OCRException(
                "PDF 处理需要 pymupdf 库，请运行: pip install pymupdf"
            )

        doc = fitz.open(stream=file_data, filetype="pdf")
        total_pages = doc.page_count
        logger.info(f"PDF OCR: {file_name} has {total_pages} pages")

        if total_pages == 0:
            doc.close()
            return ""

        texts: list[str] = []
        for i in range(total_pages):
            page = doc[i]
            # 300 DPI 保证清晰度
            pix = page.get_pixmap(dpi=300)
            png_bytes = pix.tobytes("png")

            try:
                page_text = await self._ocr_image(png_bytes, "image/png")
                if page_text.strip():
                    texts.append(page_text)
                logger.info(
                    f"PDF OCR page {i+1}/{total_pages}: {len(page_text)} chars"
                )
            except OCRException:
                logger.warning(
                    f"PDF OCR page {i+1}/{total_pages} failed, skipping"
                )
                # 单页失败不阻塞整体流程

        doc.close()

        if not texts:
            raise OCRException(
                f"PDF 所有页面 OCR 均失败（共 {total_pages} 页），请检查文件清晰度"
            )

        merged = "\n".join(texts)
        cleaned = self._post_process(merged)
        logger.info(
            f"PDF OCR done: {file_name} ({total_pages} pages) → {len(cleaned)} chars"
        )
        return cleaned

    async def _ocr_image(self, image_data: bytes, mime_type: str) -> str:
        """单张图片 OCR：base64 编码 → Chat Completions。"""
        data_url = self._encode_data_url(image_data, mime_type)

        try:
            client = create_http_client(timeout_seconds=180.0)
            try:
                body = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": data_url,
                                        "detail": "high",
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": (
                                        "<image>\n<|grounding|>"
                                        "请逐行识别并提取图片中的所有文字内容，"
                                        "包括姓名、电话、邮箱、教育经历、工作经验、"
                                        "项目经历、技能信息。不要遗漏任何文字。"
                                    ),
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
                    self.endpoint, json=body, headers=headers
                )
                response.raise_for_status()
                result = response.json()
                text = result["choices"][0]["message"]["content"] or ""
                return text

            finally:
                await client.aclose()

        except httpx.HTTPStatusError as e:
            logger.error(f"OCR API HTTP {e.response.status_code}: {e.response.text[:300]}")
            detail = e.response.text[:500] if e.response.text else ""
            if e.response.status_code == 413:
                raise OCRException("文件过大，OCR 服务无法处理，请尝试缩小文件")
            elif e.response.status_code == 429:
                raise OCRException("OCR 服务请求过于频繁，请稍后重试")
            elif e.response.status_code >= 500:
                raise OCRException(f"OCR 服务暂时不可用 ({e.response.status_code})")
            else:
                raise OCRException(f"OCR 识别失败 ({e.response.status_code}): {detail}")
        except httpx.TimeoutException:
            raise OCRException("OCR 识别超时，请尝试缩小图片后重试")
        except OCRException:
            raise
        except Exception as e:
            logger.error(f"Unexpected OCR error: {e}")
            raise OCRException(f"OCR 处理异常: {e}")

    # ---- helpers ----

    @staticmethod
    def _encode_data_url(data: bytes, mime_type: str) -> str:
        """将文件字节编码为 data URL。"""
        encoded = base64.b64encode(data).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"

    @staticmethod
    def _guess_mime_type(file_name: str) -> str:
        ext = (
            file_name.rsplit(".", 1)[-1].lower()
            if "." in file_name
            else ""
        )
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

    def _post_process(self, text: str) -> str:
        """后处理：去HTML、去连续重复行、压缩空行。"""
        if not text:
            return ""

        # 1. 去除 HTML 标签
        text = re.sub(r"<[^>]+>", "", text)

        # 2. 处理 Markdown 格式
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\[([^\]]*)\]\(.*?\)", r"\1", text)
        text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
        text = re.sub(r"#{1,6}\s*", "", text)
        text = re.sub(r"[-*]\s+", "", text)

        # 3. 去重：只去除连续重复行
        lines = text.split("\n")
        deduped = [lines[0]] if lines else []
        for line in lines[1:]:
            stripped = line.strip()
            prev_stripped = deduped[-1].strip() if deduped else ""
            if stripped == prev_stripped and stripped:
                continue
            deduped.append(line)

        text = "\n".join(deduped)

        # 4. 压缩连续空行
        text = re.sub(r"\n{3,}", "\n\n", text)

        # 5. 清理行首尾空白
        text = "\n".join(line.strip() for line in text.split("\n"))

        return text.strip()

    async def parse_resume_info(self, ocr_text: str) -> dict:
        """从 OCR 文本中提取结构化简历信息。"""
        if not ocr_text.strip() or len(ocr_text.strip()) < 10:
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

            content = (
                response.content
                if hasattr(response, "content")
                else str(response)
            )
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to parse resume info: {e}")
            return {}
