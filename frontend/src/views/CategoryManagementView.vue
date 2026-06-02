<template>
  <div class="cat-page">
    <router-link to="/knowledge-base" class="back-link">← 返回知识库</router-link>
    <div class="page-header">
      <h2 class="page-title">分类管理</h2>
      <button class="btn-primary" @click="openAdd">+ 添加分类</button>
    </div>

    <ErrorBanner v-if="error" :message="error" @dismiss="error=''" />
    <LoadingSpinner v-if="loading" text="加载中..." />

    <div v-if="!loading" class="cat-list">
      <div v-for="c in categories" :key="c.id" class="cat-row">
        <div v-if="editingId === c.id" class="edit-inline">
          <input v-model="editName" class="form-input" @keyup.enter="saveEdit(c.id)" />
          <button class="btn-sm" @click="saveEdit(c.id)">保存</button>
          <button class="btn-sm" @click="cancelEdit">取消</button>
        </div>
        <template v-else>
          <div class="cat-info">
            <span class="cat-name">{{ c.name }}</span>
            <span class="cat-desc" v-if="c.description">{{ c.description }}</span>
            <span class="cat-count">{{ catCounts[c.id] ?? '...' }} 条</span>
          </div>
          <div class="cat-actions">
            <button class="btn-sm" @click="startEdit(c)">修改</button>
            <button class="btn-sm btn-del" @click="openDel(c)">删除</button>
          </div>
        </template>
      </div>
      <div v-if="!categories.length" class="empty-state">暂无分类</div>
    </div>

    <!-- 添加分类弹窗 -->
    <div v-if="showAdd" class="dialog-overlay" @click.self="showAdd=false">
      <div class="dialog-box"><h4>添加分类</h4>
        <input v-model="addName" class="form-input" placeholder="分类名称" @keyup.enter="doAdd" />
        <div class="dialog-actions"><button class="btn-secondary" @click="showAdd=false">取消</button>
          <button class="btn-primary" @click="doAdd">确定</button></div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="delDialog.visible" class="dialog-overlay" @click.self="delDialog.visible=false">
      <div class="dialog-box"><h4>删除分类「{{ delDialog.name }}」</h4>
        <p class="del-desc">该分类下有 <strong>{{ delDialog.count }}</strong> 条问答记录</p>
        <div class="del-options">
          <label class="del-opt"><input type="radio" v-model="delKeep" :value="true" /> 保留条目（移出此分类）</label>
          <label class="del-opt"><input type="radio" v-model="delKeep" :value="false" /> 同时删除所有条目</label>
        </div>
        <div class="dialog-actions"><button class="btn-secondary" @click="delDialog.visible=false">取消</button>
          <button class="btn-danger" @click="doDel">确认删除</button></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import { knowledgeBaseApi } from '@/api/knowledgeBase'
import type { KBCategory } from '@/types/knowledgeBase'

const categories = ref<KBCategory[]>([])
const catCounts = ref<Record<string,number>>({})
const loading = ref(true), error = ref('')
const editingId = ref(''), editName = ref('')
const showAdd = ref(false), addName = ref('')
const delDialog = reactive({ visible: false, name: '', id: '', count: 0 })
const delKeep = ref(true)

onMounted(loadAll)
async function loadAll() {
  loading.value = true; error.value = ''
  try {
    const res = await knowledgeBaseApi.listCategories()
    categories.value = res.data
    // 加载每个分类的条目数
    const counts: Record<string,number> = {}
    await Promise.all(categories.value.map(async c => {
      try { const r = await knowledgeBaseApi.countCategoryItems(c.id); counts[c.id] = r.data.count } catch { counts[c.id] = 0 }
    }))
    catCounts.value = counts
  } catch (e: any) { error.value = e.message } finally { loading.value = false }
}

function openAdd() { addName.value = ''; showAdd.value = true }
async function doAdd() {
  if (!addName.value.trim()) return; showAdd.value = false
  try { await knowledgeBaseApi.createCategory({ name: addName.value.trim() }); await loadAll() } catch (e: any) { error.value = e.message }
}

function startEdit(c: KBCategory) { editingId.value = c.id; editName.value = c.name }
function cancelEdit() { editingId.value = '' }
async function saveEdit(id: string) {
  if (!editName.value.trim()) return
  try { await knowledgeBaseApi.updateCategory(id, { name: editName.value.trim() }); editingId.value = ''; await loadAll() } catch (e: any) { error.value = e.message }
}

function openDel(c: KBCategory) {
  delDialog.id = c.id; delDialog.name = c.name
  delDialog.count = catCounts.value[c.id] || 0
  delKeep.value = true; delDialog.visible = true
}
async function doDel() {
  delDialog.visible = false
  try { await knowledgeBaseApi.deleteCategory(delDialog.id, delKeep.value); await loadAll() } catch (e: any) { error.value = e.message }
}
</script>

<style scoped>
.back-link{display:inline-block;margin-bottom:16px;color:#4a90d9;text-decoration:none;font-size:14px}
.page-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.page-title{font-size:22px}
.btn-primary{padding:10px 20px;background:#1a73e8;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:14px}
.btn-sm{padding:6px 14px;font-size:12px;border:1px solid #d1d5db;border-radius:6px;background:#fff;cursor:pointer}
.btn-sm:hover{background:#f3f4f6}
.btn-del{color:#dc2626;border-color:#fca5a5;background:#fef2f2}
.btn-del:hover{background:#fee2e2}
.btn-danger{padding:8px 16px;background:#cf1322;color:#fff;border:none;border-radius:4px;cursor:pointer}
.btn-secondary{padding:8px 16px;background:#f5f5f5;border:1px solid #ddd;border-radius:4px;cursor:pointer}

.cat-list{background:#fff;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.05);overflow:hidden}
.cat-row{display:flex;justify-content:space-between;align-items:center;padding:14px 20px;border-bottom:1px solid #f3f4f6}
.cat-row:last-child{border-bottom:none}
.cat-info{display:flex;align-items:center;gap:14px;flex:1}
.cat-name{font-size:15px;font-weight:600;color:#1f2937}
.cat-desc{font-size:12px;color:#9ca3af}
.cat-count{font-size:12px;color:#6b7280;margin-left:auto}
.cat-actions{display:flex;gap:6px;margin-left:12px}
.edit-inline{display:flex;gap:8px;align-items:center}
.form-input{padding:8px 12px;border:1px solid #ddd;border-radius:4px;font-size:14px;width:200px}
.empty-state{text-align:center;color:#ccc;padding:40px;font-size:14px}

.dialog-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;z-index:1000}
.dialog-box{background:#fff;border-radius:8px;padding:24px;min-width:380px;box-shadow:0 4px 20px rgba(0,0,0,0.15)}
.dialog-box h4{font-size:16px;margin-bottom:14px}
.dialog-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:16px}
.del-desc{margin-bottom:12px;font-size:14px;color:#4b5563}
.del-options{display:flex;flex-direction:column;gap:8px;margin-bottom:8px}
.del-opt{font-size:14px;color:#374151;cursor:pointer;display:flex;align-items:center;gap:6px}
</style>
