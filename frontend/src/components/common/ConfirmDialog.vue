<template>
  <div class="dialog-overlay" v-if="visible" @click.self="$emit('cancel')">
    <div class="dialog-box">
      <h3>{{ title }}</h3>
      <p>{{ message }}</p>
      <div class="dialog-actions">
        <button class="btn-secondary" @click="$emit('cancel')">取消</button>
        <button class="btn-danger" @click="$emit('confirm')">确认</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ visible: boolean; title: string; message: string }>()
defineEmits<{ confirm: []; cancel: [] }>()
</script>

<style scoped>
.dialog-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.dialog-box { background: #fff; border-radius: 8px; padding: 24px; min-width: 360px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); }
h3 { font-size: 16px; margin-bottom: 8px; }
p { font-size: 14px; color: #666; margin-bottom: 20px; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 8px; }
.btn-secondary { padding: 8px 16px; background: #f5f5f5; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; }
.btn-danger { padding: 8px 16px; background: #cf1322; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
</style>
