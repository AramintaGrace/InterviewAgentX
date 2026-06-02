<template>
  <div class="kb-search">
    <input
      type="text"
      :value="modelValue"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      placeholder="搜索知识库问答..."
      class="search-input"
    />
  </div>
</template>

<script setup lang="ts">
defineProps<{ modelValue: string }>()
defineEmits<{ 'update:modelValue': [value: string] }>()
</script>

<style scoped>
.kb-search { margin-bottom: 16px; }
.search-input {
  width: 100%; padding: 10px 16px; border: 1px solid #ddd; border-radius: 6px;
  font-size: 14px; outline: none;
}
.search-input:focus { border-color: #4a90d9; }
</style>
