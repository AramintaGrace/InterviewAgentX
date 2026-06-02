<template>
  <div class="kb-card" @click="expanded = !expanded">
    <div class="kb-card-header">
      <span class="kb-difficulty" :class="item.difficulty">{{ difficultyLabel }}</span>
      <span class="kb-vectorized" v-if="item.is_vectorized !== undefined">
        {{ item.is_vectorized ? '✅' : '⚠️ 未向量化' }}
      </span>
      <div class="kb-actions" @click.stop>
        <button @click="$emit('edit', item.id)" title="编辑">✏️</button>
        <button @click="$emit('delete', item.id)" title="删除">🗑️</button>
      </div>
    </div>
    <p class="kb-question"><strong>Q:</strong> {{ item.question }}</p>
    <p class="kb-answer"><strong>A:</strong> {{ expanded ? item.answer : truncatedAnswer }}</p>
    <div class="kb-footer" v-if="expanded">
      <div v-if="item.tags?.length" class="kb-tags">
        <span v-for="t in item.tags" :key="t" class="kb-tag">{{ t }}</span>
      </div>
      <div class="kb-meta">
        <span v-if="item.version > 1">版本 {{ item.version }}</span>
        <span>{{ item.updated_at?.split('T')[0] }}</span>
      </div>
    </div>
    <div v-if="!expanded" class="kb-footer">
      <div v-if="item.tags?.length" class="kb-tags">
        <span v-for="t in item.tags.slice(0, 3)" :key="t" class="kb-tag">{{ t }}</span>
        <span v-if="item.tags.length > 3" class="kb-tag">+{{ item.tags.length - 3 }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{ item: any }>()
defineEmits<{ edit: [id: string]; delete: [id: string] }>()

const expanded = ref(false)

const difficultyMap: Record<string, string> = { easy: '简单', medium: '中等', hard: '困难' }
const difficultyLabel = computed(() => difficultyMap[props.item.difficulty] || '中等')

const truncatedAnswer = computed(() => {
  const text = props.item.answer || ''
  return text.length > 150 ? text.slice(0, 150) + '...' : text
})
</script>

<style scoped>
.kb-card {
  background: #fff; border-radius: 10px; padding: 18px 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05); cursor: pointer; transition: box-shadow 0.2s;
}
.kb-card:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.08); }
.kb-card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.kb-difficulty { font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 500; }
.kb-difficulty.easy { background: #f6ffed; color: #389e0d; }
.kb-difficulty.medium { background: #fffbe6; color: #d48806; }
.kb-difficulty.hard { background: #fff2f0; color: #cf1322; }
.kb-vectorized { font-size: 11px; color: #999; }
.kb-actions { margin-left: auto; display: flex; gap: 4px; }
.kb-actions button { background: none; border: none; cursor: pointer; font-size: 14px; padding: 2px 4px; }
.kb-question { font-size: 15px; font-weight: 500; line-height: 1.6; margin-bottom: 6px; color: #1f2937; }
.kb-answer { font-size: 14px; color: #6b7280; line-height: 1.7; white-space: pre-wrap; }
.kb-footer { display: flex; align-items: center; justify-content: space-between; margin-top: 10px; }
.kb-tags { display: flex; gap: 4px; flex-wrap: wrap; }
.kb-tag { font-size: 11px; padding: 2px 8px; background: #f3f4f6; border-radius: 10px; color: #6b7280; }
.kb-meta { font-size: 11px; color: #bbb; display: flex; gap: 8px; }
</style>
