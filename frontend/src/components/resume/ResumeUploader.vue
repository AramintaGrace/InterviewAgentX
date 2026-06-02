<template>
  <div class="resume-uploader">
    <div
      class="drop-zone"
      :class="{ 'drag-over': isDragOver }"
      @dragover.prevent="isDragOver = true"
      @dragleave.prevent="isDragOver = false"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <span class="upload-icon">📁</span>
      <p class="upload-text">拖拽简历文件到此处，或点击选择</p>
      <p class="upload-hint">支持 PDF、Word、图片格式（最大 20MB）</p>
    </div>
    <input
      ref="fileInput"
      type="file"
      accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
      style="display: none"
      @change="handleFileSelect"
    />

    <!-- 上传进度 -->
    <div v-if="uploading" class="upload-progress">
      <LoadingSpinner :text="progressText" />
    </div>

    <!-- 错误提示 -->
    <ErrorBanner v-if="error" :message="error" @dismiss="error = ''" />

    <!-- 上传结果 -->
    <div v-if="uploadResult" class="upload-result">
      <div class="result-header">
        <span :class="['result-badge', uploadStatusClass]">{{ uploadStatusLabel }}</span>
        <span class="result-name">{{ uploadResult.file_name }}</span>
        <span class="result-size">{{ formatSize(uploadResult.file_size_bytes) }}</span>
      </div>

      <!-- OCR 错误详情 -->
      <div v-if="uploadResult.ocr_status === 'failed'" class="ocr-error-box">
        <p class="ocr-error-title">⚠️ OCR 识别失败</p>
        <p class="ocr-error-detail">{{ uploadResult.ocr_error_msg || '未知错误' }}</p>
        <p class="ocr-error-hint">文件已保存，可稍后重试 OCR</p>
      </div>

      <!-- OCR 处理中 -->
      <div v-if="uploadResult.ocr_status === 'processing' || uploadResult.ocr_status === 'pending'" class="ocr-pending">
        <LoadingSpinner text="正在识别简历内容..." />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import { resumesApi } from '@/api/resumes'
import type { ResumeUploadResponse } from '@/types/resume'

const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20MB

const emit = defineEmits<{ uploaded: [data: ResumeUploadResponse] }>()

const fileInput = ref<HTMLInputElement>()
const isDragOver = ref(false)
const uploading = ref(false)
const progressText = ref('')
const error = ref('')
const uploadResult = ref<ResumeUploadResponse | null>(null)

const uploadStatusLabel = computed(() => {
  const s = uploadResult.value?.ocr_status
  if (s === 'completed') return '识别完成'
  if (s === 'processing' || s === 'pending') return '识别中'
  if (s === 'failed') return '识别失败'
  return '已上传'
})

const uploadStatusClass = computed(() => {
  const s = uploadResult.value?.ocr_status
  if (s === 'completed') return 'badge-success'
  if (s === 'failed') return 'badge-error'
  return 'badge-info'
})

function triggerFileInput() {
  error.value = ''
  fileInput.value?.click()
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files?.length) {
    uploadFile(target.files[0])
    // reset so same file can be re-selected
    target.value = ''
  }
}

function handleDrop(event: DragEvent) {
  isDragOver.value = false
  const file = event.dataTransfer?.files[0]
  if (file) uploadFile(file)
}

function validateFile(file: File): string | null {
  const allowedExts = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
  const ext = '.' + file.name.split('.').pop()?.toLowerCase()
  if (!allowedExts.includes(ext)) {
    return `不支持的文件格式 "${ext}"，支持: ${allowedExts.join(', ')}`
  }
  if (file.size > MAX_FILE_SIZE) {
    return `文件过大 (${formatSize(file.size)})，最大支持 20MB`
  }
  return null
}

async function uploadFile(file: File) {
  // 客户端校验
  const validationError = validateFile(file)
  if (validationError) {
    error.value = validationError
    return
  }

  uploading.value = true
  error.value = ''
  uploadResult.value = null

  // 阶段 1: 上传
  progressText.value = '正在上传文件...'
  let response: ResumeUploadResponse
  try {
    const res = await resumesApi.upload(file)
    response = res.data
  } catch (e: any) {
    error.value = e.message || '文件上传失败，请检查网络连接'
    uploading.value = false
    return
  }

  uploadResult.value = response
  emit('uploaded', response)

  // 阶段 2: 等待 OCR 完成
  if (response.ocr_status === 'pending' || response.ocr_status === 'processing') {
    progressText.value = '正在识别简历内容 (OCR)...'
    await pollOcrStatus(response.id)
  }

  uploading.value = false
}

/** 轮询 OCR 状态，最多等待 60 秒 */
async function pollOcrStatus(resumeId: string) {
  const maxRetries = 30
  const intervalMs = 2000

  for (let i = 0; i < maxRetries; i++) {
    await delay(intervalMs)
    try {
      const res = await resumesApi.getOcrStatus(resumeId)
      const data = res.data as Record<string, any>
      const status = data.ocr_status || 'unknown'
      const updated = {
        ...uploadResult.value!,
        ocr_status: status,
        ocr_error_msg: data.ocr_error_msg || uploadResult.value!.ocr_error_msg,
        ocr_raw_text: data.ocr_raw_text || uploadResult.value!.ocr_raw_text,
      }

      uploadResult.value = updated as any

      if (status === 'completed' || status === 'failed') {
        emit('uploaded', updated as any)
        return
      }
    } catch {
      // 轮询中的单次失败不中断，继续重试
    }
  }

  // 超时
  uploadResult.value = { ...uploadResult.value!, ocr_status: 'failed', ocr_error_msg: 'OCR 识别超时，请稍后重试' } as any
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

function formatSize(bytes: number): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0) + ' ' + units[i]
}
</script>

<style scoped>
.resume-uploader { max-width: 600px; }

.drop-zone {
  border: 2px dashed #ccc;
  border-radius: 12px;
  padding: 60px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafafa;
}
.drop-zone:hover, .drop-zone.drag-over {
  border-color: #4a90d9;
  background: #f0f7ff;
}

.upload-icon { font-size: 48px; display: block; margin-bottom: 12px; }
.upload-text { font-size: 16px; color: #333; }
.upload-hint { font-size: 13px; color: #999; margin-top: 8px; }

.upload-progress { margin-top: 16px; }

/* Upload result */
.upload-result {
  margin-top: 16px;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.result-header {
  display: flex;
  align-items: center;
  gap: 12px;
}
.result-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}
.badge-success { background: #e6f7e6; color: #2e7d32; }
.badge-error   { background: #fdecea; color: #c62828; }
.badge-info    { background: #e3f2fd; color: #1565c0; }

.result-name {
  font-size: 14px;
  color: #333;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.result-size {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
}

/* OCR error box */
.ocr-error-box {
  margin-top: 12px;
  padding: 12px 16px;
  background: #fff3e0;
  border: 1px solid #ffcc02;
  border-radius: 6px;
}
.ocr-error-title { font-size: 14px; font-weight: 600; color: #e65100; margin-bottom: 4px; }
.ocr-error-detail { font-size: 13px; color: #bf360c; word-break: break-word; }
.ocr-error-hint { font-size: 12px; color: #999; margin-top: 4px; }

.ocr-pending { margin-top: 12px; }
</style>
