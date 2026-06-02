<template>
  <div class="records-page">
    <h2 class="page-title">📋 面试记录</h2>

    <ErrorBanner v-if="error" :message="error" @dismiss="error = ''" />

    <!-- 成功提示 -->
    <div v-if="successMsg" class="success-banner">
      <span>{{ successMsg }}</span>
      <button @click="successMsg = ''">✕</button>
    </div>

    <!-- 筛选栏 -->
    <RecordFilter v-model="filter" @change="loadRecords" />

    <!-- Loading -->
    <LoadingSpinner v-if="loading" text="加载中..." />

    <!-- 列表 -->
    <div v-if="!loading" class="table-wrapper">
      <table class="records-table">
        <thead>
          <tr>
            <th>候选人</th>
            <th>联系方式</th>
            <th>面试日期</th>
            <th>综合评分</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in records" :key="r.candidate_id">
            <td>
              <span class="candidate-name" @click="goDetail(r.candidate_id)">
                {{ r.candidate_name }}
              </span>
              <div v-if="r.candidate_role" class="candidate-role">{{ r.candidate_role }}</div>
            </td>
            <td class="contact-cell">
              <div v-if="r.candidate_email">{{ r.candidate_email }}</div>
              <div v-if="r.candidate_phone">{{ r.candidate_phone }}</div>
              <div v-if="!r.candidate_email && !r.candidate_phone" class="no-data">—</div>
            </td>
            <td>{{ formatDate(r.interview_date) }}</td>
            <td>
              <span class="score" :class="scoreColor(r.overall_score)">
                {{ r.overall_score != null ? r.overall_score + '分' : '—' }}
              </span>
            </td>
            <td class="action-cell">
              <button class="btn-view" @click="goDetail(r.candidate_id)">查看</button>
              <button class="btn-delete" @click.stop="confirmDelete(r)">删除</button>
            </td>
          </tr>
          <tr v-if="records.length === 0">
            <td colspan="5" class="empty-row">暂无面试记录</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 删除确认 -->
    <ConfirmDialog
      :visible="deleteDialog.visible"
      title="确认删除"
      :message="`确定要删除候选人「${deleteDialog.name}」的全部记录吗？\n\n这将删除该候选人的所有简历、面试记录、回答分析、报告等数据，且不可恢复。`"
      @confirm="executeDelete"
      @cancel="deleteDialog.visible = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import RecordFilter from '@/components/records/RecordFilter.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { recordsApi } from '@/api/reports'
import type { InterviewRecord } from '@/types/report'

const router = useRouter()
const records = ref<InterviewRecord[]>([])
const loading = ref(true)
const error = ref('')
const successMsg = ref('')

const filter = reactive({ candidateName: '', dateFrom: '', dateTo: '' })

const deleteDialog = reactive({ visible: false, name: '', candidateId: '' })

onMounted(() => loadRecords())

async function loadRecords() {
  loading.value = true
  error.value = ''
  try {
    const params: any = { pageSize: 100 }
    if (filter.candidateName) params.candidateName = filter.candidateName
    if (filter.dateFrom) params.dateFrom = filter.dateFrom
    if (filter.dateTo) params.dateTo = filter.dateTo
    const res = await recordsApi.list(params)
    records.value = (res.data as any).items || []
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally { loading.value = false }
}

function goDetail(cid: string) { router.push(`/records/${cid}`) }

function confirmDelete(r: InterviewRecord) {
  deleteDialog.name = r.candidate_name
  deleteDialog.candidateId = r.candidate_id
  deleteDialog.visible = true
}

async function executeDelete() {
  deleteDialog.visible = false
  const name = deleteDialog.name
  try {
    const res = await recordsApi.deleteCandidate(deleteDialog.candidateId)
    successMsg.value = res.data.message
    records.value = records.value.filter(r => r.candidate_id !== deleteDialog.candidateId)
  } catch (e: any) {
    error.value = `删除 ${name} 失败: ${e.message || '未知错误'}`
  }
}

function formatDate(d: string) { return d?.split('T')[0] || '' }
function scoreColor(s?: number) {
  if (s == null) return ''
  if (s >= 80) return 'score-high'
  if (s >= 60) return 'score-mid'
  return 'score-low'
}
</script>

<style scoped>
.page-title { font-size: 22px; margin-bottom: 24px; }

.table-wrapper {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  overflow: hidden;
}
.records-table { width: 100%; border-collapse: collapse; }
.records-table th {
  padding: 14px 16px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}
.records-table td {
  padding: 14px 16px;
  font-size: 14px;
  color: #374151;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
}
.records-table tbody tr:hover { background: #fafbfd; }
.records-table tbody tr:last-child td { border-bottom: none; }

.candidate-name {
  color: #1f2937;
  font-weight: 600;
  cursor: pointer;
}
.candidate-name:hover { color: #4a90d9; text-decoration: underline; }
.candidate-role { font-size: 12px; color: #9ca3af; margin-top: 2px; }
.contact-cell { font-size: 13px; color: #6b7280; line-height: 1.5; }
.no-data { color: #ccc; }

.score { font-weight: 700; font-size: 15px; }
.score-high { color: #22c55e; }
.score-mid { color: #eab308; }
.score-low { color: #ef4444; }

.action-cell { display: flex; gap: 8px; }
.btn-view {
  padding: 5px 14px;
  font-size: 13px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  color: #374151;
  cursor: pointer;
}
.btn-view:hover { background: #f3f4f6; }
.btn-delete {
  padding: 5px 14px;
  font-size: 13px;
  border: 1px solid #fca5a5;
  border-radius: 6px;
  background: #fef2f2;
  color: #dc2626;
  cursor: pointer;
}
.btn-delete:hover { background: #fee2e2; }

.empty-row { text-align: center; color: #ccc; padding: 48px; font-size: 14px; }

.success-banner {
  display: flex; align-items: center; justify-content: space-between;
  background: #e8f5e9; color: #2e7d32;
  padding: 10px 16px; border-radius: 8px;
  margin-bottom: 16px; font-size: 14px;
}
.success-banner button {
  background: none; border: none; color: #2e7d32;
  cursor: pointer; font-size: 14px; padding: 0 4px;
}
</style>
