<template>
  <div class="record-table-wrapper">
    <table class="record-table">
      <thead>
        <tr>
          <th>候选人</th>
          <th>面试日期</th>
          <th>综合评分</th>
          <th>录用建议</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="record in records" :key="record.id">
          <td>{{ record.candidateName }}</td>
          <td>{{ record.interviewDate }}</td>
          <td>{{ record.overallScore }}</td>
          <td>
            <span class="recommendation-badge" :class="record.recommendation">
              {{ record.recommendationLabel }}
            </span>
          </td>
          <td>
            <router-link :to="`/records/${record.candidateId}`">查看</router-link>
          </td>
        </tr>
        <tr v-if="!records.length">
          <td colspan="5" class="empty-row">暂无记录</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
defineProps<{ records: any[] }>()
</script>

<style scoped>
.record-table-wrapper { background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow: hidden; }
.record-table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px 16px; text-align: left; font-size: 14px; border-bottom: 1px solid #f0f0f0; }
th { background: #fafafa; font-weight: 600; color: #666; }
.recommendation-badge { font-size: 12px; padding: 2px 8px; border-radius: 10px; }
.recommendation-badge.strongly_recommend, .recommendation-badge.recommend { background: #f6ffed; color: #389e0d; }
.recommendation-badge.consider { background: #fffbe6; color: #d48806; }
.recommendation-badge.not_recommend { background: #fff2f0; color: #cf1322; }
.empty-row { text-align: center; color: #ccc; padding: 40px; }
a { color: #4a90d9; text-decoration: none; }
</style>
