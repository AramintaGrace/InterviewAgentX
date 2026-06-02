export type WsMessageType = 'partial' | 'final' | 'error' | 'end'

export interface WsMessage {
  type: WsMessageType
  text?: string
  message?: string
  code?: string
  finalTranscript?: string
  durationMs?: number
}

export type WsConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error'
