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
      <p class="upload-hint">支持 PDF、Word、图片格式</p>
    </div>
    <input
      ref="fileInput"
      type="file"
      accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
      style="display: none"
      @change="handleFileSelect"
    />
    <div v-if="uploading" class="upload-progress">
      <LoadingSpinner :text="progressText" />
    </div>
    <ErrorBanner v-if="error" :message="error" @dismiss="error = ''" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'

const emit = defineEmits<{ uploaded: [data: any] }>()

const fileInput = ref<HTMLInputElement>()
const isDragOver = ref(false)
const uploading = ref(false)
const progressText = ref('')
const error = ref('')

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files?.length) {
    uploadFile(target.files[0])
  }
}

function handleDrop(event: DragEvent) {
  isDragOver.value = false
  const file = event.dataTransfer?.files[0]
  if (file) uploadFile(file)
}

async function uploadFile(file: File) {
  uploading.value = true
  progressText.value = '正在上传并识别简历...'
  error.value = ''
  try {
    // API call would go here
    emit('uploaded', { fileName: file.name })
  } catch (e: any) {
    error.value = e.message || '上传失败'
  } finally {
    uploading.value = false
  }
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
</style>
