import { ref } from 'vue'

export function useStreamingTranscript() {
  const finalText = ref('')
  const partialText = ref('')
  const isFinalizing = ref(false)

  const displayText = ref('')

  function appendPartial(text: string) {
    partialText.value = text
    updateDisplay()
  }

  function commitFinal(text: string) {
    finalText.value += (finalText.value ? '\n' : '') + text
    partialText.value = ''
    updateDisplay()
  }

  function updateDisplay() {
    displayText.value = finalText.value +
      (partialText.value ? (finalText.value ? '\n' : '') + partialText.value : '')
  }

  function finalize(fullText: string) {
    finalText.value = fullText
    partialText.value = ''
    isFinalizing.value = false
    displayText.value = fullText
  }

  function clear() {
    finalText.value = ''
    partialText.value = ''
    displayText.value = ''
    isFinalizing.value = false
  }

  return {
    finalText,
    partialText,
    isFinalizing,
    displayText,
    appendPartial,
    commitFinal,
    finalize,
    clear,
  }
}
