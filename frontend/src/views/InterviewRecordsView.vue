<template>
  <div class="records">
    <h2 class="page-title">📋 面试记录</h2>
    <RecordFilter v-model="filter" />
    <RecordTable :records="records" />
    <EmptyState v-if="!records.length" text="暂无面试记录" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import RecordFilter from '@/components/records/RecordFilter.vue'
import RecordTable from '@/components/records/RecordTable.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const filter = ref({ candidateName: '', dateFrom: '', dateTo: '' })
const records = ref([])
</script>

<style scoped>
.page-title { font-size: 22px; margin-bottom: 24px; }
</style>
