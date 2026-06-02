<template>
  <div class="transcript-display">
    <h4>
      📝 {{ modelValue ? `已输入 ${charCount} 字` : '请作答' }}
      <button v-if="modelValue" class="btn-clear" @click="$emit('update:modelValue', '')">清空</button>
    </h4>
    <textarea
      class="transcript-input"
      :value="modelValue"
      @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
      placeholder="录制语音后自动转写，或直接在此输入..."
      rows="6"
    ></textarea>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ modelValue: string }>()
defineEmits<{ 'update:modelValue': [v: string] }>()

const charCount = computed(() => props.modelValue?.length ?? 0)
</script>

<style scoped>
.transcript-display { margin-top: 16px; }
h4 {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.btn-clear {
  font-size: 12px;
  background: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 2px 10px;
  cursor: pointer;
  color: #999;
}
.btn-clear:hover { color: #cf1322; border-color: #cf1322; }
.transcript-input {
  width: 100%;
  padding: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.8;
  font-family: inherit;
  resize: vertical;
  background: #fafafa;
  transition: border-color 0.2s;
}
.transcript-input:focus {
  outline: none;
  border-color: #4a90d9;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(74,144,217,0.08);
}
.transcript-input::placeholder { color: #ccc; }
</style>
