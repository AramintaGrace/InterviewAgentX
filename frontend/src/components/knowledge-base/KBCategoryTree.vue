<template>
  <div class="category-tree">
    <h4>分类</h4>
    <ul>
      <li
        v-for="cat in categories"
        :key="cat.id"
        class="category-item"
        :class="{ active: selectedId === cat.id }"
        @click="$emit('select', cat.id)"
      >
        {{ cat.name }}
      </li>
      <li v-if="!categories.length" class="empty-cat">暂无分类</li>
    </ul>
  </div>
</template>

<script setup lang="ts">
defineProps<{ categories: any[]; selectedId?: string }>()
defineEmits<{ select: [id: string] }>()
</script>

<style scoped>
.category-tree { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
h4 { font-size: 14px; margin-bottom: 10px; }
ul { list-style: none; }
.category-item { padding: 8px 12px; cursor: pointer; font-size: 13px; border-radius: 4px; color: #555; }
.category-item:hover { background: #f5f5f5; }
.category-item.active { background: #e8f0fe; color: #1a73e8; }
.empty-cat { font-size: 12px; color: #ccc; padding: 8px; }
</style>
