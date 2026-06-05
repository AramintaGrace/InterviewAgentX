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
      <p class="upload-hint">支持 PDF、Word、图片（最大 20MB/文件）</p>
      <p class="upload-hint-multi">📸 多页简历？可一次选择多张图片，系统智能合并！</p>
    </div>
    <input
      ref="fileInput"
      type="file"
      accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
      multiple
      style="display: none"
      @change="handleFileSelect"
    />

    <!-- 已选文件预览 -->
    <div v-if="selectedFiles.length > 0 && !uploading" class="selected-files">
      <div class="files-header">
        <span>已选择 {{ selectedFiles.length }} 个文件</span>
        <button class="btn-clear" @click="clearSelection">✕ 清除</button>
      </div>
      <div v-for="(f, i) in selectedFiles" :key="i" class="file-item">
        <span class="file-icon">📄</span>
        <span class="file-name">{{ f.name }}</span>
        <span class="file-size">{{ formatSize(f.size) }}</span>
        <button class="btn-remove" @click.stop="removeFile(i)">✕</button>
      </div>
      <button
        class="btn-upload-all"
        :disabled="uploading"
        @click="uploadAllFiles"
      >
        {{ selectedFiles.length > 1 ? `🚀 上传并智能合并 ${selectedFiles.length} 张图片` : '📤 上传简历' }}
      </button>
    </div>

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

      <!-- 合并信息 -->
      <div v-if="selectedFiles.length > 1 && uploadResult.ocr_status === 'completed'" class="merge-info">
        ✅ 已智能合并 {{ selectedFiles.length }} 张图片为一份完整简历
      </div>

      <div v-if="uploadResult.ocr_status === 'failed'" class="ocr-error-box">
        <p class="ocr-error-title">⚠️ OCR 识别失败</p>
        <p class="ocr-error-detail">{{ uploadResult.ocr_error_msg || '未知错误' }}</p>
        <p class="ocr-error-hint">文件已保存，可稍后重试</p>
      </div>

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

const MAX_FILE_SIZE = 20 * 1024 * 1024

const emit = defineEmits<{ uploaded: [data: ResumeUploadResponse] }>()

const fileInput = ref<HTMLInputElement>()
const selectedFiles = ref<File[]>([])
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
    for (let i = 0; i < target.files.length; i++) {
      addFile(target.files[i])
    }
    target.value = ''
  }
}

function handleDrop(event: DragEvent) {
  isDragOver.value = false
  const dt = event.dataTransfer
  if (dt?.files) {
    for (let i = 0; i < dt.files.length; i++) {
      addFile(dt.files[i])
    }
  }
}

function addFile(file: File) {
  const err = validateFile(file)
  if (err) {
    error.value = err
    return
  }
  // Prevent duplicates by name+size
  const exists = selectedFiles.value.some(f => f.name === file.name && f.size === file.size)
  if (!exists && selectedFiles.value.length < 10) {
    selectedFiles.value.push(file)
  }
}

function removeFile(index: number) {
  selectedFiles.value.splice(index, 1)
}

function clearSelection() {
  selectedFiles.value = []
  error.value = ''
}

function validateFile(file: File): string | null {
  const ext = '.' + file.name.split('.').pop()?.toLowerCase()
  const allowed = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
  if (!allowed.includes(ext)) return `不支持 "${ext}"`
  if (file.size > MAX_FILE_SIZE) return `${file.name} 过大 (${formatSize(file.size)})`
  return null
}

async function uploadAllFiles() {
  if (!selectedFiles.value.length) return

  uploading.value = true
  error.value = ''
  uploadResult.value = null
  progressText.value = `正在上传 ${selectedFiles.value.length} 个文件...`

  try {
    const isMulti = selectedFiles.value.length > 1
    let response: ResumeUploadResponse

    if (isMulti) {
      progressText.value = `正在上传并OCR识别 ${selectedFiles.value.length} 张图片...`
      const res = await resumesApi.uploadMultiple(selectedFiles.value)
      response = res.data
      progressText.value = '正在智能合并多页简历...'
    } else {
      const res = await resumesApi.upload(selectedFiles.value[0])
      response = res.data
    }

    uploadResult.value = response
    emit('uploaded', response)

    if (response.ocr_status === 'pending' || response.ocr_status === 'processing') {
      progressText.value = isMulti ? '正在LLM智能合并 + OCR...' : 'OCR识别中...'
      await pollOcrStatus(response.id)
    }
  } catch (e: any) {
    error.value = e.message || '上传失败'
  } finally {
    uploading.value = false
  }
}

async function pollOcrStatus(resumeId: string) {
  for (let i = 0; i < 45; i++) {  // up to 90s
    await delay(2000)
    try {
      const res = await resumesApi.getOcrStatus(resumeId)
      const data = res.data as Record<string, any>
      uploadResult.value = {
        ...uploadResult.value!,
        ocr_status: data.ocr_status,
        ocr_error_msg: data.ocr_error_msg || uploadResult.value!.ocr_error_msg,
        ocr_raw_text: data.ocr_raw_text || uploadResult.value!.ocr_raw_text,
      } as any
      if (data.ocr_status === 'completed' || data.ocr_status === 'failed') {
        emit('uploaded', uploadResult.value!)
        return
      }
    } catch { /* continue polling */ }
  }
}

function delay(ms: number) { return new Promise(r => setTimeout(r, ms)) }

function formatSize(bytes: number): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0) + ' ' + units[i]
}
</script>

<style scoped>
.resume-uploader { max-width: 640px; }

.drop-zone {
  border: 2px dashed #ccc;
  border-radius: 12px;
  padding: 48px 20px;
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
.upload-hint-multi { font-size: 13px; color: #4a90d9; margin-top: 4px; }

/* Selected files */
.selected-files {
  margin-top: 16px;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.files-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}
.btn-clear {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 13px;
}
.btn-clear:hover { color: #666; }

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  font-size: 13px;
  border-bottom: 1px solid #f5f5f5;
}
.file-item:last-child { border-bottom: none; }
.file-icon { font-size: 16px; flex-shrink: 0; }
.file-name { flex: 1; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-size { color: #999; font-size: 12px; white-space: nowrap; }
.btn-remove {
  background: none;
  border: none;
  color: #ccc;
  cursor: pointer;
  font-size: 12px;
  padding: 2px 4px;
}
.btn-remove:hover { color: #e74c3c; }

.btn-upload-all {
  margin-top: 12px;
  width: 100%;
  padding: 10px;
  background: #4a90d9;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-upload-all:hover { background: #357abd; }
.btn-upload-all:disabled { background: #ccc; cursor: not-allowed; }

.upload-progress { margin-top: 16px; }

/* Result */
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
.result-size { font-size: 12px; color: #999; white-space: nowrap; }

/* Merge info */
.merge-info {
  margin-top: 10px;
  padding: 8px 12px;
  background: #e8f5e9;
  border-radius: 6px;
  font-size: 13px;
  color: #2e7d32;
}

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

@media (max-width: 640px) {
  .drop-zone { padding: 32px 12px; }
  .upload-text { font-size: 14px; }
}
</style>
