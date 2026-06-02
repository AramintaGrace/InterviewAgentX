import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { WsMessage, WsConnectionState } from '@/types/websocket'

export const useSTTStore = defineStore('stt', () => {
  const connectionState = ref<WsConnectionState>('disconnected')
  const transcript = ref('')
  const partialTranscript = ref('')
  const isRecording = ref(false)
  const recordingDuration = ref(0)
  const ws = ref<WebSocket | null>(null)

  function setRecording(recording: boolean) {
    isRecording.value = recording
  }

  function addPartialText(text: string) {
    partialTranscript.value = text
  }

  function addFinalText(text: string) {
    transcript.value += (transcript.value ? '\n' : '') + text
    partialTranscript.value = ''
  }

  function clearTranscript() {
    transcript.value = ''
    partialTranscript.value = ''
  }

  function reset() {
    connectionState.value = 'disconnected'
    transcript.value = ''
    partialTranscript.value = ''
    isRecording.value = false
    recordingDuration.value = 0
    ws.value = null
  }

  return {
    connectionState,
    transcript,
    partialTranscript,
    isRecording,
    recordingDuration,
    ws,
    setRecording,
    addPartialText,
    addFinalText,
    clearTranscript,
    reset,
  }
})
