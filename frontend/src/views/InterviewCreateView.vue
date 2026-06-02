<template>
  <div class="interview-create">
    <h2 class="page-title">🎤 创建面试会话</h2>
    <div class="create-form">
      <div class="form-group">
        <label>选择候选人</label>
        <select v-model="form.candidateId" class="form-input">
          <option value="">-- 请选择 --</option>
        </select>
      </div>
      <div class="form-group">
        <label>选择简历</label>
        <select v-model="form.resumeId" class="form-input">
          <option value="">-- 请选择 --</option>
        </select>
      </div>
      <div class="form-group">
        <label>题目来源</label>
        <QuestionSourceSelector v-model="form.questionSource" />
      </div>
      <div class="form-group">
        <label>题目数量</label>
        <input type="number" v-model="form.totalQuestions" min="1" max="20" class="form-input" />
      </div>
      <button class="btn-primary" @click="createSession">创建面试</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import QuestionSourceSelector from '@/components/interview/QuestionSourceSelector.vue'

const router = useRouter()

const form = reactive({
  candidateId: '',
  resumeId: '',
  questionSource: 'resume',
  totalQuestions: 5,
})

function createSession() {
  router.push(`/interviews/session-${Date.now()}`)
}
</script>

<style scoped>
.page-title { font-size: 22px; margin-bottom: 24px; }
.create-form { background: #fff; padding: 24px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); max-width: 600px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 14px; font-weight: 500; margin-bottom: 6px; }
.form-input { width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
.btn-primary { padding: 10px 24px; background: #4a90d9; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
.btn-primary:hover { background: #357abd; }
</style>
