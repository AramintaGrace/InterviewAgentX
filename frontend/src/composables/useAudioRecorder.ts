import { ref, onUnmounted, type Ref } from 'vue'

interface UseAudioRecorderOptions {
  onChunk?: (chunk: ArrayBuffer) => void
  mimeType?: string
  chunkIntervalMs?: number
}

export function useAudioRecorder(options: UseAudioRecorderOptions = {}) {
  const {
    onChunk,
    mimeType = 'audio/webm;codecs=opus',
    chunkIntervalMs = 200,
  } = options

  const isRecording = ref(false)
  const isPaused = ref(false)
  const duration = ref(0)
  const error = ref<string | null>(null)

  let mediaRecorder: MediaRecorder | null = null
  let stream: MediaStream | null = null
  let timerInterval: ReturnType<typeof setInterval> | null = null
  let startTime = 0

  async function start() {
    error.value = null
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      })

      mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported(mimeType) ? mimeType : 'audio/webm',
      })

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && onChunk) {
          event.data.arrayBuffer().then((buffer) => {
            onChunk(buffer)
          })
        }
      }

      mediaRecorder.onstop = () => {
        stopTimer()
        stream?.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start(chunkIntervalMs)
      isRecording.value = true
      startTime = Date.now()
      startTimer()
    } catch (e: any) {
      error.value = e.message || '无法访问麦克风'
      console.error('Audio recorder error:', e)
    }
  }

  function pause() {
    if (mediaRecorder?.state === 'recording') {
      mediaRecorder.pause()
      isPaused.value = true
      stopTimer()
    }
  }

  function resume() {
    if (mediaRecorder?.state === 'paused') {
      mediaRecorder.resume()
      isPaused.value = false
      startTimer()
    }
  }

  function stop() {
    if (mediaRecorder?.state !== 'inactive') {
      mediaRecorder?.stop()
    }
    isRecording.value = false
    isPaused.value = false
  }

  function startTimer() {
    timerInterval = setInterval(() => {
      duration.value = Math.round((Date.now() - startTime) / 1000)
    }, 1000)
  }

  function stopTimer() {
    if (timerInterval) {
      clearInterval(timerInterval)
      timerInterval = null
    }
    duration.value = Math.round((Date.now() - startTime) / 1000)
  }

  onUnmounted(() => {
    stop()
  })

  return {
    isRecording,
    isPaused,
    duration,
    error,
    start,
    pause,
    resume,
    stop,
  }
}
