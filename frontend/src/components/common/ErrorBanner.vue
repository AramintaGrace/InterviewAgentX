<template>
  <div class="error-banner" v-if="message">
    <span class="error-icon">⚠️</span>
    <span class="error-text">{{ message }}</span>
    <button class="error-close" @click="$emit('dismiss')">&times;</button>
  </div>
</template>

<script setup lang="ts">
defineProps<{ message: string }>()
defineEmits<{ dismiss: [] }>()
</script>

<style scoped>
.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 6px;
  margin-bottom: 16px;
}
.error-icon { font-size: 16px; }
.error-text { flex: 1; color: #cf1322; font-size: 14px; }
.error-close { background: none; border: none; font-size: 18px; cursor: pointer; color: #999; }
</style>
