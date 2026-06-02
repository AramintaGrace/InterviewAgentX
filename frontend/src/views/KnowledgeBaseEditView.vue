<template>
  <div class="kb-edit">
    <h2 class="page-title">{{ isEdit ? '编辑问答' : '添加问答' }}</h2>
    <form @submit.prevent="save" class="kb-form">
      <div class="form-group">
        <label>分类</label>
        <select v-model="form.categoryId" class="form-input">
          <option value="">-- 请选择 --</option>
        </select>
      </div>
      <div class="form-group">
        <label>问题</label>
        <textarea v-model="form.question" rows="3" class="form-input" placeholder="请输入面试问题"></textarea>
      </div>
      <div class="form-group">
        <label>答案</label>
        <textarea v-model="form.answer" rows="8" class="form-input" placeholder="请输入标准答案"></textarea>
      </div>
      <div class="form-group">
        <label>标签</label>
        <input v-model="tagInput" class="form-input" placeholder="输入标签后回车" @keydown.enter.prevent="addTag" />
        <div class="tag-list">
          <span v-for="t in form.tags" :key="t" class="tag">{{ t }} <button @click="removeTag(t)">&times;</button></span>
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
        <button type="submit" class="btn-primary">保存</button>
        <button type="button" class="btn-secondary" @click="$router.back()">取消</button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isEdit = computed(() => !!route.params.itemId)

const form = reactive({
  categoryId: '',
  question: '',
  answer: '',
  tags: [] as string[],
  difficulty: 'medium',
})

const tagInput = ref('')

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

function save() {
  // API call
}
</script>

<style scoped>
.page-title { font-size: 22px; margin-bottom: 24px; }
.kb-form { background: #fff; padding: 24px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); max-width: 700px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 14px; font-weight: 500; margin-bottom: 6px; }
.form-input { width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
.tag-list { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px; }
.tag { background: #e8f0fe; color: #1a73e8; padding: 2px 8px; border-radius: 12px; font-size: 12px; display: flex; align-items: center; gap: 4px; }
.tag button { background: none; border: none; color: #666; cursor: pointer; font-size: 14px; }
.form-actions { display: flex; gap: 12px; margin-top: 20px; }
.btn-primary { padding: 10px 24px; background: #4a90d9; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
.btn-secondary { padding: 10px 24px; background: #f5f5f5; color: #666; border: 1px solid #ddd; border-radius: 6px; cursor: pointer; }
</style>
