"""Prompt for deduplicating overlapping multi-page resume OCR texts.

This is only invoked when consecutive pages have >30% word overlap.
The direct concatenation already preserves ALL content — this step only
removes duplicate content between pages.
"""

RESUME_MERGE_PROMPT = """你是一个简历文本去重助手。以下简历的多页OCR结果存在内容重叠，请去重合并。

## 规则

1. **保留全部独有内容**：每页独有的信息必须全部保留，不能删除、改写或总结。
2. **只删除重复**：仅当两段文字表述完全相同或高度相似（>90%）时才删除其中一个。
3. **标题允许重复**：如"教育背景""工作经历"等标题在每页都可能出现，保留每个出现。
4. **保持原文**：不修正拼写、不改写句子、不润色文字。
5. **按页序排列**：保持第1页→第2页→...的自然顺序。

## 原始OCR文本
{ocr_texts}

## 输出
直接输出去重合并后的完整简历文本，不要任何解释。
"""
