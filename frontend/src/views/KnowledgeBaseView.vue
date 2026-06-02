<template>
  <div class="knowledge-base">
    <div class="page-header">
      <h2 class="page-title">📚 知识库</h2>
      <router-link to="/knowledge-base/create" class="btn-primary">+ 添加问答</router-link>
    </div>
    <KBSearchBar v-model="searchQuery" />
    <div class="kb-layout">
      <KBCategoryTree :categories="categories" class="kb-sidebar" />
      <div class="kb-list">
        <KBCard v-for="item in items" :key="item.id" :item="item" @edit="editItem" @delete="deleteItem" />
        <EmptyState v-if="!items.length" text="暂无知识库条目" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import KBSearchBar from '@/components/knowledge-base/KBSearchBar.vue'
import KBCategoryTree from '@/components/knowledge-base/KBCategoryTree.vue'
import KBCard from '@/components/knowledge-base/KBCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const router = useRouter()
const searchQuery = ref('')
const categories = ref([])
const items = ref([])

function editItem(id: string) {
  router.push(`/knowledge-base/${id}/edit`)
}

function deleteItem(id: string) {
  // API call
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-title { font-size: 22px; }
.btn-primary { padding: 10px 20px; background: #4a90d9; color: #fff; border: none; border-radius: 6px; text-decoration: none; font-size: 14px; }
.kb-layout { display: flex; gap: 24px; margin-top: 16px; }
.kb-sidebar { width: 200px; flex-shrink: 0; }
.kb-list { flex: 1; display: flex; flex-direction: column; gap: 12px; }
</style>
