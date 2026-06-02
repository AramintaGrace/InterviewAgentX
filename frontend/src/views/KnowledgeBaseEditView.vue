<template>
  <div class="kb-edit">
    <h2 class="page-title">{{ isEdit ? '编辑问答' : '添加问答' }}</h2>

    <ErrorBanner v-if="error" :message="error" @dismiss="error = ''" />

    <form @submit.prevent="save" class="kb-form">
      <div class="form-group">
        <label>分类</label>
        <select v-model="form.category_id" class="form-input">
          <option value="">-- 请选择 --</option>
          <option v-for="c in store.categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>
      <div class="form-group">
        <label>题目</label>
        <input v-model="form.title" class="form-input" placeholder="简短标题，用于快速识别，如「SQL注入原理」" maxlength="300" />
      </div>
      <div class="form-group">
        <label>问题</label>
        <textarea v-model="form.question" rows="3" class="form-input" placeholder="请输入完整的面试问题"></textarea>
      </div>
      <div class="form-group">
        <label>答案</label>
        <textarea v-model="form.answer" rows="10" class="form-input" placeholder="请输入标准答案"></textarea>
      </div>
      <div class="form-group">
        <label>标签</label>
        <input v-model="tagInput" class="form-input" placeholder="输入标签后回车" @keydown.enter.prevent="addTag" />
        <div v-if="form.tags.length" class="tag-list">
          <span v-for="t in form.tags" :key="t" class="tag">{{ t }} <button type="button" @click="removeTag(t)">&times;</button></span>
        </div>
      </div>
      <div class="form-group">
        <label>难度</label>
        <select v-model="form.difficulty" class="form-input">
          <option value="easy">简单</option>
          <option value="medium">中等</option>
          <option value="hard">困难</option>
        </select>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn-primary" :disabled="saving">
          {{ saving ? '⏳ 保存中...' : '💾 保存' }}
        </button>
        <button type="button" class="btn-secondary" @click="$router.back()">取消</button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase'
import { knowledgeBaseApi } from '@/api/knowledgeBase'

const route = useRoute()
const router = useRouter()
const store = useKnowledgeBaseStore()
const isEdit = computed(() => !!route.params.itemId)
const error = ref('')
const saving = ref(false)

const form = reactive({
  category_id: '',
  title: '',
  question: '',
  answer: '',
  tags: [] as string[],
  difficulty: 'medium' as string,
})

const tagInput = ref('')

onMounted(async () => {
  await store.loadCategories()
  if (isEdit.value) {
    await loadItem()
  }
})

async function loadItem() {
  try {
    const res = await knowledgeBaseApi.getItem(route.params.itemId as string)
    const d = res.data as any
    form.category_id = d.category_id || ''
    form.title = d.title || ''
    form.question = d.question || ''
    form.answer = d.answer || ''
    form.tags = d.tags || []
    form.difficulty = d.difficulty || 'medium'
  } catch (e: any) {
    error.value = e.message || '加载条目失败'
  }
}

function addTag() {
  const tag = tagInput.value.trim()
  if (tag && !form.tags.includes(tag)) {
    form.tags.push(tag)
  }
  tagInput.value = ''
}

function removeTag(tag: string) {
  form.tags = form.tags.filter(t => t !== tag)
}

async function save() {
  if (!form.question.trim() || !form.answer.trim()) {
    error.value = '问题和答案不能为空'
    return
  }

  saving.value = true
  error.value = ''

  const data = {
    category_id: form.category_id || undefined,
    title: form.title.trim() || undefined,
    question: form.question.trim(),
    answer: form.answer.trim(),
    tags: form.tags,
    difficulty: form.difficulty as any,
  }

  try {
    if (isEdit.value) {
      await store.updateItem(route.params.itemId as string, data as any)
    } else {
      await store.createItem(data as any)
    }
    router.push('/knowledge-base')
  } catch (e: any) {
    error.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.page-title { font-size: 22px; margin-bottom: 24px; }
.kb-form { background: #fff; padding: 28px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); max-width: 700px; }
.form-group { margin-bottom: 18px; }
.form-group label { display: block; font-size: 14px; font-weight: 600; margin-bottom: 6px; color: #374151; }
.form-input { width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; font-family: inherit; }
.form-input:focus { outline: none; border-color: #4a90d9; box-shadow: 0 0 0 3px rgba(74,144,217,0.1); }
textarea.form-input { resize: vertical; }
.tag-list { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.tag { background: #e8f0fe; color: #1a73e8; padding: 3px 10px; border-radius: 12px; font-size: 12px; display: flex; align-items: center; gap: 4px; }
.tag button { background: none; border: none; color: #999; cursor: pointer; font-size: 14px; line-height: 1; }
.form-actions { display: flex; gap: 12px; margin-top: 24px; }
.btn-primary { padding: 10px 28px; background: #1a73e8; color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; }
.btn-primary:hover:not(:disabled) { background: #1557b0; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-secondary { padding: 10px 24px; background: #f5f5f5; color: #666; border: 1px solid #ddd; border-radius: 8px; cursor: pointer; font-size: 14px; }
</style>
