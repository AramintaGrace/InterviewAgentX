import { ref, onUnmounted } from 'vue'
import type { WsMessage, WsConnectionState } from '@/types/websocket'

export function useWebSocket(sessionId: string, questionId: string) {
  const ws = ref<WebSocket | null>(null)
  const connectionState = ref<WsConnectionState>('disconnected')
  const transcript = ref('')
  const partialText = ref('')
  const error = ref<string | null>(null)

  function connect() {
    connectionState.value = 'connecting'
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/ws/stt/${sessionId}/${questionId}`

    ws.value = new WebSocket(url)
    ws.value.binaryType = 'arraybuffer'

    ws.value.onopen = () => {
      connectionState.value = 'connected'
    }

    ws.value.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data)
        switch (msg.type) {
          case 'partial':
            partialText.value = msg.text || ''
            break
          case 'final':
            if (msg.text) {
              transcript.value += (transcript.value ? '\n' : '') + msg.text
            }
            partialText.value = ''
            break
          case 'end':
            if (msg.finalTranscript) {
              transcript.value = msg.finalTranscript
            }
            break
          case 'error':
            error.value = msg.message || 'STT error'
            break
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    ws.value.onerror = () => {
      connectionState.value = 'error'
      error.value = 'WebSocket connection error'
    }

    ws.value.onclose = () => {
      connectionState.value = 'disconnected'
    }
  }

  function sendAudioChunk(chunk: ArrayBuffer) {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(chunk)
    }
  }

  function endRecording() {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send('END_RECORDING')
    }
  }

  function disconnect() {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    connectionState,
    transcript,
    partialText,
    error,
    connect,
    sendAudioChunk,
    endRecording,
    disconnect,
  }
}
