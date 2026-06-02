<template>
  <div class="record-filter">
    <input
      type="text"
      v-model="local.name"
      placeholder="候选人姓名"
      class="filter-input"
      @keyup.enter="$emit('change')"
    />
    <input
      type="date"
      v-model="local.date"
      class="filter-input"
      @change="$emit('change')"
    />
    <button class="btn-filter" @click="$emit('change')">🔍 搜索</button>
    <button v-if="hasFilter" class="btn-clear" @click="clearFilter">✕ 清除</button>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch, computed } from 'vue'

const props = defineProps<{ modelValue: { candidateName: string; dateFrom: string; dateTo: string } }>()
const emit = defineEmits<{ 'update:modelValue': [v: any]; change: [] }>()

const local = reactive({ name: props.modelValue.candidateName, date: props.modelValue.dateFrom || props.modelValue.dateTo || '' })

const hasFilter = computed(() => local.name || local.date)

watch(local, () => {
  emit('update:modelValue', {
    candidateName: local.name,
    dateFrom: local.date,
    dateTo: local.date,
  })
}, { deep: true })

watch(() => props.modelValue, (v) => {
  local.name = v.candidateName
  local.date = v.dateFrom || v.dateTo || ''
}, { deep: true })

function clearFilter() {
  local.name = ''
  local.date = ''
  emit('change')
}
</script>

<style scoped>
.record-filter { display: flex; gap: 10px; margin-bottom: 20px; align-items: center; }
.filter-input { padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; outline: none; width: 180px; }
.filter-input:focus { border-color: #4a90d9; }
.btn-filter {
  padding: 8px 16px; background: #1a73e8; color: #fff;
  border: none; border-radius: 6px; cursor: pointer; font-size: 13px;
}
.btn-filter:hover { background: #1557b0; }
.btn-clear {
  padding: 8px 14px; background: #f5f5f5; color: #666;
  border: 1px solid #ddd; border-radius: 6px; cursor: pointer; font-size: 13px;
}
.btn-clear:hover { background: #eee; }
</style>
