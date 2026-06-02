<template>
  <div class="kb-pool-selector">
    <div class="pool-header">
      <h4>题目池 <span class="pool-count">({{ poolIds.length }} 题已选)</span></h4>
      <button v-if="poolIds.length" class="btn-clear-pool" @click="$emit('update:poolIds',[])">清空</button>
    </div>

    <!-- 搜索 + 分类筛选 -->
    <div class="pool-search-row">
      <input v-model="search" class="form-input search-input" placeholder="搜索知识库题目..." @input="debounceSearch" />
      <select v-model="filterCat" class="form-input cat-input" @change="searchItems">
        <option value="">全部分类</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
    </div>

    <LoadingSpinner v-if="loading" text="加载中..." />

    <!-- KB 条目列表 -->
    <div v-if="!loading" class="pool-items">
      <div v-for="it in kbItems" :key="it.id"
        class="pool-item"
        :class="{ selected: poolIds.includes(it.id) }"
        @click="toggleItem(it.id)"
      >
        <input type="checkbox" :checked="poolIds.includes(it.id)" class="pool-check" @click.stop />
        <div class="pool-item-body">
          <span class="pool-item-title">{{ it.title || it.question }}</span>
          <span class="pool-item-cat">{{ catName(it.category_id) }}</span>
          <span class="pool-item-diff" :class="it.difficulty">{{ diffMap[it.difficulty] || it.difficulty }}</span>
        </div>
      </div>
      <div v-if="kbItems.length === 0" class="pool-empty">没有匹配的知识库条目</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { knowledgeBaseApi } from '@/api/knowledgeBase'
import type { KBCategory, KBItem } from '@/types/knowledgeBase'

const props = defineProps<{
  poolIds: string[]
  categories: KBCategory[]
}>()
const emit = defineEmits<{ 'update:poolIds': [ids: string[]] }>()

const kbItems = ref<KBItem[]>([])
const loading = ref(false)
const search = ref('')
const filterCat = ref('')
let t: any = null

const diffMap: Record<string,string> = { easy:'简单', medium:'中等', hard:'困难' }
function catName(cid?: string) { return cid ? props.categories.find(c => c.id === cid)?.name || '' : '' }

onMounted(() => searchItems())

async function searchItems() {
  loading.value = true
  try {
    const res = await knowledgeBaseApi.listItems({
      search: search.value || undefined,
      category_id: filterCat.value || undefined,
      vectorization_status: 'vectorized',
      pageSize: 50,
    })
    kbItems.value = (res.data as any).items || []
  } catch { kbItems.value = [] }
  finally { loading.value = false }
}

function debounceSearch() { clearTimeout(t); t = setTimeout(searchItems, 300) }

function toggleItem(id: string) {
  const ids = [...props.poolIds]
  const idx = ids.indexOf(id)
  if (idx >= 0) ids.splice(idx, 1)
  else ids.push(id)
  emit('update:poolIds', ids)
}
</script>

<style scoped>
.kb-pool-selector {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 8px;
  padding: 14px; margin-bottom: 16px; max-width: 640px;
}
.pool-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.pool-header h4 { font-size: 14px; color: #374151; }
.pool-count { font-weight: 400; color: #6366f1; font-size: 13px; }
.btn-clear-pool { font-size: 12px; padding: 2px 10px; border: 1px solid #ddd; border-radius: 4px; background: #fff; color: #999; cursor: pointer; }
.btn-clear-pool:hover { color: #cf1322; border-color: #cf1322; }

.pool-search-row { display: flex; gap: 8px; margin-bottom: 10px; }
.search-input { flex: 1; }
.cat-input { width: 140px; flex-shrink: 0; }
.form-input { padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }
.form-input:focus { outline: none; border-color: #4a90d9; }

.pool-items { max-height: 280px; overflow-y: auto; border: 1px solid #f0f0f0; border-radius: 6px; }
.pool-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 10px;
  border-bottom: 1px solid #f5f5f5; cursor: pointer; transition: background 0.1s;
}
.pool-item:hover { background: #f9fafb; }
.pool-item.selected { background: #eef2ff; }
.pool-item:last-child { border-bottom: none; }
.pool-check { flex-shrink: 0; }
.pool-item-body { flex: 1; min-width: 0; display: flex; align-items: center; gap: 8px; }
.pool-item-title { font-size: 13px; color: #1f2937; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.pool-item-cat { font-size: 11px; color: #9ca3af; white-space: nowrap; }
.pool-item-diff { font-size: 10px; padding: 1px 6px; border-radius: 6px; white-space: nowrap; }
.pool-item-diff.easy { background: #e8f5e9; color: #2e7d32; }
.pool-item-diff.medium { background: #fffbe6; color: #d48806; }
.pool-item-diff.hard { background: #fdecea; color: #c62828; }
.pool-empty { text-align: center; color: #ccc; padding: 24px; font-size: 13px; }
</style>
