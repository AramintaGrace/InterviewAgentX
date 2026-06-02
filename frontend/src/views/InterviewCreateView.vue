<template>
  <div class="interview-create">
    <h2 class="page-title">🎤 创建面试会话</h2>

    <ErrorBanner v-if="error" :message="error" @dismiss="error = ''" />

    <div class="create-form">
      <!-- 候选人 -->
      <div class="form-group">
        <label>选择候选人</label>
        <select v-model="form.candidateId" class="form-input">
          <option value="">-- 请选择 --</option>
          <option v-for="c in candidates" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>

      <!-- 简历 -->
      <div class="form-group">
        <label>选择简历</label>
        <select v-model="form.resumeId" class="form-input">
          <option value="">-- 请选择 --</option>
          <option v-for="r in filteredResumes" :key="r.id" :value="r.id">
            {{ r.file_name }} ({{ r.ocr_status === 'completed' ? '已识别' : r.ocr_status }})
          </option>
        </select>
        <p v-if="filteredResumes.length === 0 && resumes.length > 0" class="form-hint">
          当前候选人没有简历，请先上传简历
        </p>
      </div>

      <!-- 题目来源 -->
      <div class="form-group">
        <label>题目来源</label>
        <QuestionSourceSelector v-model="form.questionSource" />
      </div>

      <!-- resume 模式：题目数量 -->
      <div v-if="form.questionSource === 'resume'" class="form-group">
        <label>题目数量</label>
        <input type="number" v-model.number="form.totalQuestions" min="1" max="20" class="form-input" />
      </div>

      <!-- KB 或 mixed 模式：题目池 -->
      <KBPoolSelector
        v-if="form.questionSource !== 'resume'"
        v-model:pool-ids="poolIds"
        :categories="kbCategories"
      />

      <!-- KB 或 mixed 模式：分类选择 + 数量 -->
      <div v-if="form.questionSource !== 'resume'" class="kb-config-section">
        <!-- KB only：总数量 -->
        <div v-if="form.questionSource === 'knowledge_base'" class="form-group">
          <label>题目总数</label>
          <input type="number" v-model.number="form.totalQuestions" min="1" max="20" class="form-input" />
        </div>

        <!-- mixed：resume 占比 -->
        <div v-if="form.questionSource === 'mixed'" class="form-group">
          <label>总题目数</label>
          <input type="number" v-model.number="form.totalQuestions" min="2" max="20" class="form-input" />
        </div>
        <div v-if="form.questionSource === 'mixed'" class="form-group">
          <label>简历题目占比: {{ form.resumeRatio }}%</label>
          <input type="range" v-model.number="form.resumeRatio" min="10" max="90" step="10" class="slider" />
          <div class="ratio-hint">
            简历题 {{ resumeCount }} 道 · 知识库题 {{ kbCount }} 道
          </div>
        </div>

        <!-- 分类选择 -->
        <div class="form-group">
          <label>知识库分类选择（留空从全部随机）</label>
          <div v-if="kbCategories.length === 0" class="no-cat">暂无分类，将从全部知识点随机出题</div>
          <div v-for="(cfg, idx) in kbConfigs" :key="idx" class="kb-cat-row">
            <select v-model="cfg.categoryId" class="form-input cat-select">
              <option value="">全部</option>
              <option v-for="c in kbCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
            <input type="number" v-model.number="cfg.count" min="0" :max="form.totalQuestions" class="form-input count-input" />
            <span class="count-label">题</span>
            <button v-if="kbConfigs.length > 1" class="btn-remove" @click="removeCat(idx)">✕</button>
          </div>
          <button class="btn-add-cat" @click="addCat">+ 添加分类</button>
        </div>
      </div>

      <button class="btn-primary" @click="createSession" :disabled="creating">
        {{ creating ? '⏳ 创建中...' : '🚀 创建面试并生成题目' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import QuestionSourceSelector from '@/components/interview/QuestionSourceSelector.vue'
import KBPoolSelector from '@/components/interview/KBPoolSelector.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import { resumesApi } from '@/api/resumes'
import { interviewsApi } from '@/api/interviews'
import { knowledgeBaseApi } from '@/api/knowledgeBase'
import { useInterviewStore } from '@/stores/interview'
import type { ResumeInfo, Candidate } from '@/types/resume'
import type { KBCategory } from '@/types/knowledgeBase'

const router = useRouter()
const route = useRoute()
const store = useInterviewStore()

const candidates = ref<Candidate[]>([])
const resumes = ref<ResumeInfo[]>([])
const kbCategories = ref<KBCategory[]>([])
const error = ref('')
const creating = ref(false)
const poolIds = ref<string[]>([])

const form = reactive({
  candidateId: '',
  resumeId: '',
  questionSource: 'resume' as string,
  totalQuestions: 5,
  resumeRatio: 60,
})

type CatCfg = { categoryId: string; count: number }
const kbConfigs = reactive<CatCfg[]>([{ categoryId: '', count: 2 }])

const filteredResumes = computed(() => {
  if (!form.candidateId) return resumes.value
  return resumes.value.filter(r => r.candidate_id === form.candidateId)
})

const resumeCount = computed(() => Math.max(1, Math.round(form.totalQuestions * form.resumeRatio / 100)))
const kbCount = computed(() => form.totalQuestions - resumeCount.value)

function addCat() { kbConfigs.push({ categoryId: '', count: 2 }) }
function removeCat(idx: number) { kbConfigs.splice(idx, 1) }

onMounted(async () => {
  const queryResumeId = route.query.resume_id as string
  if (queryResumeId) form.resumeId = queryResumeId

  try {
    const [cRes, rRes, catRes] = await Promise.all([
      resumesApi.listCandidates({ pageSize: 100 }),
      resumesApi.listResumes({ pageSize: 100 }),
      knowledgeBaseApi.listCategories(),
    ])
    candidates.value = (cRes.data as any).items || []
    resumes.value = (rRes.data as any).items || []
    kbCategories.value = catRes.data || []

    if (queryResumeId && resumes.value.length) {
      const resume = resumes.value.find(r => r.id === queryResumeId)
      if (resume?.candidate_id) form.candidateId = resume.candidate_id
    }
  } catch (e: any) {
    error.value = '加载数据失败: ' + (e.message || '未知错误')
  }
})

async function createSession() {
  if (!form.candidateId || !form.resumeId) {
    error.value = '请选择候选人和简历'; return
  }

  creating.value = true; error.value = ''

  // 重置 store，避免新会话沿用旧数据
  store.reset()

  try {
    const sessionRes = await interviewsApi.create({
      candidate_id: form.candidateId, resume_id: form.resumeId,
      question_source: form.questionSource as any,
      total_questions: form.totalQuestions,
    })
    const session = sessionRes.data

    // 构造 generate 请求
    const genData: any = {
      source: form.questionSource,
      count: form.totalQuestions,
    }
    if (form.questionSource !== 'resume') {
      genData.kb_configs = kbConfigs.filter(c => c.count > 0).map(c => ({
        category_id: c.categoryId || null,
        count: c.count,
      }))
      genData.pool_ids = poolIds.value
    }
    if (form.questionSource === 'mixed') {
      genData.resume_ratio = form.resumeRatio
    }

    await interviewsApi.generateQuestions(session.id, genData)
    await interviewsApi.start(session.id)
    await store.loadQuestions(session.id)
    store.currentSession = session
    router.push(`/interviews/${session.id}`)
  } catch (e: any) {
    error.value = e.message || '创建面试失败'
  } finally { creating.value = false }
}
</script>

<style scoped>
.page-title { font-size: 22px; margin-bottom: 24px; }
.create-form { max-width: 640px; background: #fff; padding: 28px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
.form-group { margin-bottom: 20px; }
.form-group label { display: block; font-size: 14px; font-weight: 600; margin-bottom: 6px; color: #374151; }
.form-input { width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; background: #fff; }
.form-input:focus { outline: none; border-color: #4a90d9; box-shadow: 0 0 0 3px rgba(74,144,217,0.1); }
.form-hint { font-size: 12px; color: #e65100; margin-top: 4px; }

.kb-config-section { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
.slider { width: 100%; }
.ratio-hint { font-size: 13px; color: #6b7280; text-align: center; margin-top: 4px; }
.kb-cat-row { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.cat-select { flex: 1; }
.count-input { width: 70px; }
.count-label { font-size: 14px; color: #666; }
.btn-remove { background: none; border: none; color: #cf1322; cursor: pointer; font-size: 16px; padding: 0 4px; }
.btn-add-cat { padding: 6px 14px; font-size: 13px; border: 1px dashed #d1d5db; border-radius: 6px; background: #fff; color: #6b7280; cursor: pointer; }
.btn-add-cat:hover { border-color: #4a90d9; color: #4a90d9; }
.no-cat { font-size: 13px; color: #9ca3af; }

.btn-primary {
  width: 100%; padding: 12px 0; font-size: 15px; font-weight: 600;
  background: #1a73e8; color: #fff; border: none; border-radius: 8px; cursor: pointer; transition: background 0.2s;
}
.btn-primary:hover:not(:disabled) { background: #1557b0; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
