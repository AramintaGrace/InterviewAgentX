<template>
  <div class="kb-card">
    <div class="kb-card-header">
      <span class="kb-difficulty" :class="item.difficulty">{{ difficultyLabel }}</span>
      <span class="kb-category">{{ item.categoryName || '未分类' }}</span>
      <div class="kb-actions">
        <button @click="$emit('edit', item.id)" title="编辑">✏️</button>
        <button @click="$emit('delete', item.id)" title="删除">🗑️</button>
      </div>
    </div>
    <p class="kb-question"><strong>Q:</strong> {{ item.question }}</p>
    <p class="kb-answer"><strong>A:</strong> {{ truncatedAnswer }}</p>
    <div v-if="item.tags?.length" class="kb-tags">
      <span v-for="t in item.tags" :key="t" class="kb-tag">{{ t }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ item: any }>()

defineEmits<{ edit: [id: string]; delete: [id: string] }>()

const difficultyMap: Record<string, string> = { easy: '简单', medium: '中等', hard: '困难' }
const difficultyLabel = computed(() => difficultyMap[props.item.difficulty] || '中等')

const truncatedAnswer = computed(() => {
  const text = props.item.answer || ''
  return text.length > 150 ? text.slice(0, 150) + '...' : text
})
</script>

<style scoped>
.kb-card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.kb-card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.kb-difficulty { font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.kb-difficulty.easy { background: #f6ffed; color: #389e0d; }
.kb-difficulty.medium { background: #fffbe6; color: #d48806; }
.kb-difficulty.hard { background: #fff2f0; color: #cf1322; }
.kb-category { font-size: 12px; color: #999; flex: 1; }
.kb-actions { display: flex; gap: 4px; }
.kb-actions button { background: none; border: none; cursor: pointer; font-size: 14px; }
.kb-question { font-size: 14px; line-height: 1.6; margin-bottom: 6px; }
.kb-answer { font-size: 13px; color: #666; line-height: 1.5; }
.kb-tags { display: flex; gap: 4px; margin-top: 8px; flex-wrap: wrap; }
.kb-tag { font-size: 11px; padding: 2px 8px; background: #f0f0f0; border-radius: 10px; color: #666; }
</style>
