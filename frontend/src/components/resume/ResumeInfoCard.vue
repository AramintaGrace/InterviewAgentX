<template>
  <div class="resume-info-card" v-if="resume">
    <h3>📄 简历详情</h3>

    <!-- OCR 状态条 -->
    <div :class="['ocr-status-bar', `ocr-${ocrStatus}`]">
      <span class="ocr-status-icon">{{ ocrStatusIcon }}</span>
      <span class="ocr-status-text">{{ ocrStatusText }}</span>
      <span v-if="resume.ocr_error_msg" class="ocr-error-msg">{{ resume.ocr_error_msg }}</span>
    </div>

    <!-- 文件信息 -->
    <div class="file-info">
      <span class="file-name">{{ resume.file_name }}</span>
      <span class="file-meta">{{ formatSize(resume.file_size_bytes) }} · {{ resume.mime_type }}</span>
    </div>

    <!-- 姓名醒目展示 -->
    <div v-if="parsed?.name" class="candidate-name-hero">
      <div class="avatar">{{ parsed.name.charAt(0) }}</div>
      <div class="name-detail">
        <span class="candidate-name">{{ parsed.name }}</span>
        <span v-if="parsed.email" class="candidate-contact">{{ parsed.email }}{{ parsed.phone ? ' · ' + parsed.phone : '' }}</span>
        <span v-else-if="parsed.phone" class="candidate-contact">{{ parsed.phone }}</span>
      </div>
    </div>

    <!-- 解析出的简历信息 -->
    <div v-if="parsed" class="info-section">
      <h4>📋 解析信息</h4>
      <div class="info-grid" v-if="parsed.email || parsed.phone || parsed.name">
        <div class="info-item" v-if="parsed.email"><label>邮箱</label><span>{{ parsed.email }}</span></div>
        <div class="info-item" v-if="parsed.phone"><label>电话</label><span>{{ parsed.phone }}</span></div>
      </div>

      <!-- 教育经历 -->
      <div v-if="parsed.education?.length" class="sub-section">
        <h4>🎓 教育经历</h4>
        <div v-for="(edu, i) in parsed.education" :key="i" class="list-item">
          <span class="item-title">{{ edu.school }}</span>
          <span class="item-sub"> — {{ edu.degree }}{{ edu.year ? ' (' + edu.year + ')' : '' }}</span>
        </div>
      </div>

      <!-- 工作经历 -->
      <div v-if="parsed.experience?.length" class="sub-section">
        <h4>💼 工作经历</h4>
        <div v-for="(exp, i) in parsed.experience" :key="i" class="list-item">
          <span class="item-title">{{ exp.role }}</span>
          <span class="item-sub"> @ {{ exp.company }}{{ exp.duration ? ' · ' + exp.duration : '' }}</span>
          <p v-if="exp.description" class="item-desc">{{ exp.description }}</p>
        </div>
      </div>

      <!-- 项目 -->
      <div v-if="parsed.projects?.length" class="sub-section">
        <h4>🚀 项目</h4>
        <div v-for="(proj, i) in parsed.projects" :key="i" class="list-item">
          <span class="item-title">{{ proj.name }}</span>
          <p v-if="proj.description" class="item-desc">{{ proj.description }}</p>
          <div v-if="proj.tech_stack?.length" class="skill-tags">
            <span v-for="tech in proj.tech_stack" :key="tech" class="skill-tag">{{ tech }}</span>
          </div>
        </div>
      </div>

      <!-- 技能 -->
      <div v-if="parsed.skills?.length" class="sub-section">
        <h4>🛠 技能</h4>
        <div class="skill-tags">
          <span v-for="skill in parsed.skills" :key="skill" class="skill-tag">{{ skill }}</span>
        </div>
      </div>
    </div>

    <!-- OCR 文本预览 -->
    <div v-if="hasRawText" class="sub-section">
      <h4>📝 识别原文</h4>
      <pre class="raw-text" v-text="cleanRawText"></pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ResumeInfo, ParsedResumeData } from '@/types/resume'

const props = defineProps<{ resume: ResumeInfo | any }>()

const parsed = computed<ParsedResumeData | null>(() => {
  return props.resume?.parsed_data || null
})

const ocrStatus = computed(() => props.resume?.ocr_status || 'unknown')

const ocrStatusIcon = computed(() => {
  switch (ocrStatus.value) {
    case 'completed': return '✅'
    case 'processing': return '⏳'
    case 'pending': return '🕐'
    case 'failed': return '❌'
    default: return '❓'
  }
})

const ocrStatusText = computed(() => {
  switch (ocrStatus.value) {
    case 'completed': return 'OCR 识别完成'
    case 'processing': return '正在识别...'
    case 'pending': return '等待识别'
    case 'failed': return '识别失败'
    default: return '状态未知'
  }
})

const hasRawText = computed(() => {
  const raw = props.resume?.ocr_raw_text || ''
  // 过滤纯 HTML 空表格这类无意义输出
  const cleaned = raw.replace(/<[^>]+>/g, '').replace(/\s+/g, '').trim()
  return cleaned.length > 0
})

const cleanRawText = computed(() => {
  const raw = props.resume?.ocr_raw_text || ''
  if (!raw) return '(空)'
  // 先去掉 HTML 标签
  const stripped = raw.replace(/<[^>]+>/g, '')
  // 截取前 3000 字符
  const truncated = stripped.length > 3000 ? stripped.slice(0, 3000) + '\n...' : stripped
  return truncated
})

function formatSize(bytes: number): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0) + ' ' + units[i]
}
</script>

<style scoped>
.resume-info-card {
  max-width: 720px;
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  margin-top: 24px;
}
h3 { font-size: 16px; margin-bottom: 16px; }
h4 { font-size: 14px; margin: 16px 0 8px; color: #555; }

/* OCR status bar */
.ocr-status-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 13px;
}
.ocr-completed { background: #e8f5e9; color: #2e7d32; }
.ocr-processing, .ocr-pending { background: #e3f2fd; color: #1565c0; }
.ocr-failed { background: #fdecea; color: #c62828; }
.ocr-unknown { background: #f5f5f5; color: #666; }
.ocr-error-msg {
  flex: 1;
  text-align: right;
  font-size: 12px;
  opacity: 0.8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* File info */
.file-info {
  font-size: 13px;
  color: #888;
  margin-bottom: 16px;
}
.file-name { margin-right: 12px; font-weight: 500; color: #444; }

/* 姓名醒目展示 */
.candidate-name-hero {
  display: flex;
  align-items: center;
  gap: 14px;
  background: linear-gradient(135deg, #f0f7ff 0%, #e8f0fe 100%);
  border: 1px solid #d2e3fc;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 20px;
}
.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1a73e8, #4a90d9);
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.name-detail {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.candidate-name {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a1a;
}
.candidate-contact {
  font-size: 13px;
  color: #666;
}

.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.info-item label { display: block; font-size: 12px; color: #999; }
.info-item span { font-size: 14px; color: #333; }

.sub-section { margin-top: 12px; }
.list-item { margin-bottom: 8px; }
.item-title { font-weight: 500; color: #333; }
.item-sub { font-size: 13px; color: #666; }
.item-desc { font-size: 13px; color: #777; margin: 4px 0 0 0; }

.skill-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px; }
.skill-tag { background: #e8f0fe; color: #1a73e8; padding: 3px 10px; border-radius: 12px; font-size: 12px; }

.raw-text {
  background: #f8f9fa;
  border: 1px solid #eee;
  border-radius: 6px;
  padding: 12px;
  font-size: 12px;
  line-height: 1.5;
  max-height: 240px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
