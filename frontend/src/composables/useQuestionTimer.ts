import { ref, onUnmounted } from 'vue'

export function useQuestionTimer(maxSeconds: number = 300) {
  const elapsed = ref(0)
  const isRunning = ref(false)
  const isExpired = ref(false)
  let interval: ReturnType<typeof setInterval> | null = null

  function start() {
    elapsed.value = 0
    isRunning.value = true
    isExpired.value = false
    interval = setInterval(() => {
      elapsed.value++
      if (elapsed.value >= maxSeconds) {
        isExpired.value = true
        stop()
      }
    }, 1000)
  }

  function stop() {
    isRunning.value = false
    if (interval) {
      clearInterval(interval)
      interval = null
    }
  }

  function reset() {
    stop()
    elapsed.value = 0
    isExpired.value = false
  }

  const formattedTime = ref('00:00')
  setInterval(() => {
    if (isRunning.value) {
      const m = Math.floor(elapsed.value / 60)
      const s = elapsed.value % 60
      formattedTime.value = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
    }
  }, 250)

  onUnmounted(() => {
    if (interval) clearInterval(interval)
  })

  return {
    elapsed,
    isRunning,
    isExpired,
    formattedTime,
    start,
    stop,
    reset,
  }
}
