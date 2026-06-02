import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUIStore = defineStore('ui', () => {
  const globalLoading = ref(false)
  const globalError = ref<string | null>(null)
  const sidebarCollapsed = ref(false)

  function setLoading(loading: boolean) {
    globalLoading.value = loading
  }

  function setError(message: string | null) {
    globalError.value = message
  }

  function clearError() {
    globalError.value = null
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  return {
    globalLoading,
    globalError,
    sidebarCollapsed,
    setLoading,
    setError,
    clearError,
    toggleSidebar,
  }
})
