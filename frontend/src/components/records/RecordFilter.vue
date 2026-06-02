<template>
  <div class="record-filter">
    <input
      type="text"
      :value="modelValue.candidateName"
      @input="update('candidateName', ($event.target as HTMLInputElement).value)"
      placeholder="候选人姓名"
      class="filter-input"
    />
    <input
      type="date"
      :value="modelValue.dateFrom"
      @input="update('dateFrom', ($event.target as HTMLInputElement).value)"
      class="filter-input"
    />
    <input
      type="date"
      :value="modelValue.dateTo"
      @input="update('dateTo', ($event.target as HTMLInputElement).value)"
      class="filter-input"
    />
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ modelValue: { candidateName: string; dateFrom: string; dateTo: string } }>()
const emit = defineEmits<{ 'update:modelValue': [value: any] }>()

function update(field: string, value: string) {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}
</script>

<style scoped>
.record-filter { display: flex; gap: 12px; margin-bottom: 16px; }
.filter-input { padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; outline: none; }
.filter-input:focus { border-color: #4a90d9; }
</style>
