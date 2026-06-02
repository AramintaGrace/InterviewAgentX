<template>
  <div class="transcript-display">
    <h4>📝 语音转写结果</h4>
    <div class="transcript-box">
      <p v-if="text">{{ text }}</p>
      <p v-else class="placeholder">等待语音输入...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ text: string }>()
</script>

<style scoped>
.transcript-display { margin-top: 16px; }
h4 { font-size: 14px; margin-bottom: 8px; }
.transcript-box { background: #f9f9fb; border-radius: 6px; padding: 16px; min-height: 80px; }
.transcript-box p { font-size: 14px; line-height: 1.8; }
.placeholder { color: #ccc; font-style: italic; }
</style>
