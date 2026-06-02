<template>
  <div class="audio-recorder">
    <button
      class="record-btn"
      :class="{ recording: isRecording }"
      @click="toggleRecording"
      :disabled="isProcessing"
    >
      <span class="record-icon">{{ icon }}</span>
      <span class="record-label">{{ label }}</span>
    </button>
    <div v-if="isRecording" class="record-timer">{{ formattedTime }}</div>
    <div v-if="recorderError" class="recorder-error">{{ recorderError }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAudioRecorder } from '@/composables/useAudioRecorder'
import { transcribeAudio } from '@/api/stt'

const emit = defineEmits<{
  transcript: [text: string]
}>()

const isProcessing = ref(false)
const recorderError = ref('')
let audioChunks: Blob[] = []

const {
  isRecording,
  duration,
  error,
  start: startRecorder,
  stop: stopRecorder,
} = useAudioRecorder({
  mimeType: 'audio/webm;codecs=opus',
  chunkIntervalMs: 1000,
  onChunk: (chunk: ArrayBuffer) => {
    audioChunks.push(new Blob([chunk], { type: 'audio/webm' }))
  },
})

watch(error, (val) => { if (val) recorderError.value = val })

const formattedTime = computed(() => {
  const m = Math.floor(duration.value / 60)
  const s = duration.value % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
})

const icon = computed(() => {
  if (isProcessing.value) return '⏳'
  if (isRecording.value) return '⏹'
  return '🎙️'
})

const label = computed(() => {
  if (isProcessing.value) return '转写中...'
  if (isRecording.value) return '停止录音'
  return '开始录音'
})

async function toggleRecording() {
  recorderError.value = ''
  if (isRecording.value) {
    await stopAndTranscribe()
  } else {
    audioChunks = []
    await startRecorder()
  }
}

async function stopAndTranscribe() {
  stopRecorder()
  if (audioChunks.length === 0) return

  isProcessing.value = true
  const fullBlob = new Blob(audioChunks, { type: 'audio/webm' })

  try {
    const text = await transcribeAudio(fullBlob, `recording-${Date.now()}.webm`)
    if (text && text.trim()) {
      emit('transcript', text.trim())
    } else {
      recorderError.value = '未识别到语音内容，请重新录制'
    }
  } catch (e: any) {
    recorderError.value = e.message || '语音转写失败，请手动输入文字'
  } finally {
    isProcessing.value = false
  }
}
</script>

<style scoped>
.audio-recorder { display: flex; align-items: center; gap: 16px; padding: 16px 0; flex-wrap: wrap; }
.record-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 24px; border: 2px solid #4a90d9; border-radius: 50px;
  background: #fff; cursor: pointer; transition: all 0.2s;
  font-size: 14px;
}
.record-btn:hover { background: #f0f7ff; }
.record-btn.recording { border-color: #cf1322; background: #fff2f0; animation: pulse 1.5s infinite; }
.record-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.record-icon { font-size: 20px; }
.record-timer { font-size: 16px; font-weight: 600; color: #cf1322; }
.recorder-error { width: 100%; font-size: 13px; color: #cf1322; }
@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
</style>
