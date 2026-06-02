<template>
  <div class="source-selector">
    <label class="source-option" :class="{ active: modelValue === 'resume' }">
      <input type="radio" value="resume" :checked="modelValue === 'resume'" @change="$emit('update:modelValue', 'resume')" />
      <span>📄 简历经历/项目</span>
    </label>
    <label class="source-option" :class="{ active: modelValue === 'knowledge_base' }">
      <input type="radio" value="knowledge_base" :checked="modelValue === 'knowledge_base'" @change="$emit('update:modelValue', 'knowledge_base')" />
      <span>📚 知识库</span>
    </label>
    <label class="source-option" :class="{ active: modelValue === 'mixed' }">
      <input type="radio" value="mixed" :checked="modelValue === 'mixed'" @change="$emit('update:modelValue', 'mixed')" />
      <span>🔀 混合模式</span>
    </label>
  </div>
</template>

<script setup lang="ts">
defineProps<{ modelValue: string }>()
defineEmits<{ 'update:modelValue': [value: string] }>()
</script>

<style scoped>
.source-selector { display: flex; gap: 12px; }
.source-option {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 16px; border: 1px solid #ddd; border-radius: 6px;
  cursor: pointer; transition: all 0.2s;
}
.source-option.active { border-color: #4a90d9; background: #f0f7ff; }
.source-option input[type="radio"] { display: none; }
.source-option span { font-size: 14px; }
</style>
