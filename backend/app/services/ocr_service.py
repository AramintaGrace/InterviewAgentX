"""OCR service — 硅基流动 deepseek-ai/DeepSeek-OCR via Files API.

流程：上传图片到 SF Files API → 拿到 OSS URL → Chat Completions OCR → 后处理去重。
避免 base64 数据 URL 过大导致的问题。
"""

import logging
import re
from typing import Optional

import httpx

from app.config import Settings
from app.utils.exceptions import OCRException
from app.utils.proxy import create_http_client

logger = logging.getLogger(__name__)

FILES_API = "https://api.siliconflow.cn/v1/files"
FILES_BASE = "https://api.siliconflow.cn/v1"


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

        1. 上传文件到 SiliconFlow Files API
        2. 用文件 OSS URL 调 Chat Completions OCR
        3. 后处理去重
        """
        mime_type = self._guess_mime_type(file_name)

        # Step 1: Upload to Files API
        file_id, file_url = await self._upload_file(file_data, file_name, mime_type)
        logger.info(f"OCR: uploaded {file_name} ({len(file_data)} bytes) → file_id={file_id}")

        try:
            # Step 2: OCR via Chat Completions
            raw = await self._ocr_call(file_url)
            # Step 3: Post-process
            cleaned = self._post_process(raw)
            logger.info(f"OCR: extracted {len(cleaned)} chars from {file_name}")
            return cleaned

        finally:
            # Cleanup: delete uploaded file (best-effort, ignore failures)
            try:
                await self._delete_file(file_id)
            except Exception:
                pass

    async def _upload_file(self, file_data: bytes, filename: str, mime_type: str) -> tuple[str, str]:
        """上传文件到 SiliconFlow，返回 (file_id, file_url)。"""
        try:
            client = create_http_client(timeout_seconds=120.0)
            try:
                response = await client.post(
                    FILES_API,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files={"file": (filename, file_data, mime_type)},
                    data={"purpose": "ocr"},
                )
                response.raise_for_status()
                result = response.json()
                data = result.get("data", {})
                return data["id"], data["object"]

            finally:
                await client.aclose()

        except httpx.HTTPStatusError as e:
            logger.error(f"SF Files upload failed: {e.response.status_code} {e.response.text[:300]}")
            raise OCRException(f"文件上传失败 ({e.response.status_code})，请稍后重试")
        except Exception as e:
            logger.error(f"SF Files upload error: {type(e).__name__}: {e}")
            raise OCRException(f"文件上传异常: {type(e).__name__}: {e}")

    async def _ocr_call(self, file_url: str) -> str:
        """调 Chat Completions 做 OCR。"""
        try:
            client = create_http_client(timeout_seconds=180.0)
            try:
                body = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": file_url}},
                                {
                                    "type": "text",
                                    "text": "请逐行提取图片中的所有文字，包括姓名、电话、邮箱、教育经历、工作经验、项目经历、技能信息。不要遗漏任何文字。",
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

                response = await client.post(self.endpoint, json=body, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"] or ""

            finally:
                await client.aclose()

        except httpx.HTTPStatusError as e:
            logger.error(f"OCR API HTTP {e.response.status_code}: {e.response.text}")
            detail = e.response.text[:500] if e.response.text else ""
            if e.response.status_code == 413:
                raise OCRException("文件过大，OCR 服务无法处理")
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

    async def _delete_file(self, file_id: str) -> None:
        """删除上传的临时文件（best-effort）。"""
        try:
            client = create_http_client(timeout_seconds=30.0)
            try:
                await client.delete(
                    f"{FILES_BASE}/files/{file_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
            finally:
                await client.aclose()
        except Exception:
            pass  # 清理失败不抛异常

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

        # 3. 去重：只去除连续重复行（保留跨页相同的标题名如"教育背景"）
        lines = text.split("\n")
        deduped = [lines[0]] if lines else []
        for line in lines[1:]:
            stripped = line.strip()
            prev_stripped = deduped[-1].strip() if deduped else ""
            # 只比较完全相同的连续行
            if stripped == prev_stripped and stripped:
                continue
            deduped.append(line)

        text = "\n".join(deduped)

        # 4. 压缩连续空行
        text = re.sub(r"\n{3,}", "\n\n", text)

        # 5. 清理行首尾空白
        text = "\n".join(line.strip() for line in text.split("\n"))

        return text.strip()

    @staticmethod
    def _guess_mime_type(file_name: str) -> str:
        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        mapping = {
            "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "webp": "image/webp", "gif": "image/gif", "bmp": "image/bmp",
            "tiff": "image/tiff", "tif": "image/tiff", "pdf": "application/pdf",
        }
        return mapping.get(ext, "application/octet-stream")

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
            content = response.content if hasattr(response, "content") else str(response)
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to parse resume info: {e}")
            return {}
