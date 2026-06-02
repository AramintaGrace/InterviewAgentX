<template>
  <div class="audio-recorder">
    <button
      class="record-btn"
      :class="{ recording: isRecording }"
      @click="toggleRecording"
      :disabled="isProcessing"
    >
      <span class="record-icon">{{ isRecording ? '⏹' : '🎙️' }}</span>
      <span class="record-label">{{ buttonLabel }}</span>
    </button>
    <div v-if="isRecording" class="record-timer">{{ formattedTime }}</div>
    <div v-if="isRecording" class="audio-wave">
      <span v-for="i in 20" :key="i" class="wave-bar" :style="{ animationDelay: `${i * 0.05}s` }"></span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'

const emit = defineEmits<{ transcript: [text: string] }>()

const isRecording = ref(false)
const isProcessing = ref(false)
const elapsedSeconds = ref(0)
let timerInterval: ReturnType<typeof setInterval> | null = null

const buttonLabel = computed(() => {
  if (isProcessing.value) return '处理中...'
  if (isRecording.value) return '停止录音'
  return '开始录音'
})

const formattedTime = computed(() => {
  const m = Math.floor(elapsedSeconds.value / 60)
  const s = elapsedSeconds.value % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
})

function toggleRecording() {
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

function startRecording() {
  isRecording.value = true
  elapsedSeconds.value = 0
  timerInterval = setInterval(() => { elapsedSeconds.value++ }, 1000)
  // Web Audio API recording logic would go here
}

function stopRecording() {
  isRecording.value = false
  isProcessing.value = true
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
  // Simulate STT result
  setTimeout(() => {
    isProcessing.value = false
    emit('transcript', '这是模拟的语音转文字结果...')
  }, 1500)
}

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})
</script>

<style scoped>
.audio-recorder { display: flex; align-items: center; gap: 16px; padding: 16px 0; }
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
.audio-wave { display: flex; align-items: center; gap: 2px; height: 30px; }
.wave-bar { width: 3px; height: 10px; background: #4a90d9; border-radius: 1px; animation: wave 0.6s ease-in-out infinite alternate; }
@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
@keyframes wave { from { height: 5px; } to { height: 20px; } }
</style>
