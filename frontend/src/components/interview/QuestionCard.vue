<template>
  <div class="question-card">
    <div class="question-header">
      <span class="question-number">第 {{ question.question_order }} 题</span>
      <span class="question-badge" :class="question.source_type">
        {{ sourceLabel }}
      </span>
    </div>
    <p class="question-text">{{ question.question_text }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ question: { question_text: string; source_type: string; question_order: number } }>()

const sourceLabel = computed(() => {
  const map: Record<string, string> = {
    resume_experience: '简历经历',
    resume_project: '简历项目',
    knowledge_base: '知识库',
  }
  return map[props.question.source_type] || props.question.source_type
})
</script>

<style scoped>
.question-card { background: #f9f9fb; border-radius: 8px; padding: 20px; margin-bottom: 16px; }
.question-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.question-number { font-size: 13px; color: #999; }
.question-badge { font-size: 12px; padding: 2px 8px; border-radius: 10px; }
.question-badge.resume_experience, .question-badge.resume_project { background: #e8f0fe; color: #1a73e8; }
.question-badge.knowledge_base { background: #e6f8e6; color: #389e0d; }
.question-text { font-size: 16px; line-height: 1.6; color: #333; }
</style>
