<template>
  <div class="kb-page">
    <ErrorBanner v-if="error" :message="error" @dismiss="error = ''" />
    <div v-if="successMsg" class="success-banner">{{ successMsg }}<button @click="successMsg=''">✕</button></div>

    <div class="page-header">
      <h2 class="page-title">知识库</h2>
      <div class="header-actions">
        <router-link to="/knowledge-base/categories" class="btn-outline">分类管理</router-link>
        <router-link to="/knowledge-base/create" class="btn-primary">+ 添加问答</router-link>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-row">
      <KBSearchBar v-model="search" @input="debounceSearch" />
      <select v-model="filterCat" class="filter-select" @change="loadItems">
        <option value="">全部分类</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <select v-model="filterVec" class="filter-select" @change="loadItems">
        <option value="">全部向量化状态</option>
        <option value="vectorized">已向量化</option>
        <option value="not_vectorized">未向量化</option>
        <option value="needs_revectorize">待重新向量化</option>
      </select>
    </div>

    <!-- 批量操作 -->
    <div v-if="selected.length" class="batch-bar">
      <span>已选 {{ selected.length }} 项</span>
      <button class="btn-sm" @click="showCatDlg=true">修改分类</button>
      <button class="btn-sm btn-danger" @click="confirmBatchDel">批量删除</button>
      <button class="btn-sm" @click="doBatchRevectorize">批量向量化</button>
    </div>

    <LoadingSpinner v-if="loading" text="加载中..." />

    <div v-if="!loading" class="table-wrapper">
      <table class="kb-table">
        <thead><tr>
          <th style="width:40px"><input type="checkbox" :checked="allSelected" @change="toggleAll" /></th>
          <th>题目</th><th style="width:90px">分类</th><th style="width:70px">难度</th>
          <th style="width:100px">向量化状态</th><th style="width:100px">操作</th>
        </tr></thead>
        <tbody>
          <tr v-for="it in items" :key="it.id">
            <td><input type="checkbox" :checked="selected.includes(it.id)" @change="toggle(it.id)" /></td>
            <td>
              <router-link :to="`/knowledge-base/${it.id}/edit`" class="item-link">{{ it.title || it.question }}</router-link>
              <div class="item-sub" v-if="it.title && it.question && it.title !== it.question">{{ it.question }}</div>
              <div v-if="it.tags?.length" class="tags-row">
                <span v-for="t in it.tags.slice(0,3)" :key="t" class="mini-tag">{{ t }}</span>
              </div>
            </td>
            <td class="cell-muted">{{ catName(it.category_id) }}</td>
            <td><span class="diff" :class="it.difficulty">{{ diffMap[it.difficulty]||it.difficulty }}</span></td>
            <td><span class="vec-badge" :class="vecCls(it)">{{ vecLbl(it) }}</span></td>
            <td class="cell-actions">
              <router-link :to="`/knowledge-base/${it.id}/edit`" class="btn-act">修改</router-link>
              <button v-if="it.needs_revectorize||!it.is_vectorized" class="btn-act" @click="vecOne(it.id)">向量化</button>
              <button class="btn-act btn-del" @click="confirmOne(it)">删除</button>
            </td>
          </tr>
          <tr v-if="!items.length"><td colspan="6" class="empty-row">暂无条目</td></tr>
        </tbody>
      </table>
    </div>

    <div v-if="total>pageSize" class="pagination">
      <button :disabled="page<=1" @click="changePage(page-1)">上一页</button>
      <span>{{ page }} / {{ Math.ceil(total/pageSize) }}</span>
      <button :disabled="page>=Math.ceil(total/pageSize)" @click="changePage(page+1)">下一页</button>
    </div>

    <!-- 删除确认 -->
    <ConfirmDialog :visible="del.visible" title="确认删除" :message="del.msg" @confirm="doDel" @cancel="del.visible=false" />

    <!-- 分类选择弹窗 -->
    <div v-if="showCatDlg" class="dialog-overlay" @click.self="showCatDlg=false">
      <div class="dialog-box"><h4>修改分类</h4>
        <select v-model="batchCat" class="form-input"><option value="">清除分类</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <div class="dialog-actions"><button class="btn-secondary" @click="showCatDlg=false">取消</button>
          <button class="btn-primary" @click="doBatchCat">确定</button></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import KBSearchBar from '@/components/knowledge-base/KBSearchBar.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { knowledgeBaseApi } from '@/api/knowledgeBase'
import type { KBCategory, KBItem } from '@/types/knowledgeBase'

const items = ref<KBItem[]>([]), categories = ref<KBCategory[]>([])
const loading = ref(true), error = ref(''), successMsg = ref('')
const page = ref(1), pageSize = 20, total = ref(0)
const search = ref(''), filterCat = ref(''), filterVec = ref('')
const selected = ref<string[]>([]), batchCat = ref(''), showCatDlg = ref(false)
const del = reactive({ visible: false, msg: '', id: '', batch: false })

const allSelected = computed(() => items.value.length>0 && selected.value.length===items.value.length)

onMounted(async () => { await Promise.all([loadCats(), loadItems()]) })
async function loadCats() { try { const r=await knowledgeBaseApi.listCategories(); categories.value=r.data } catch {} }
async function loadItems() {
  loading.value=true; error.value=''
  try { const r=await knowledgeBaseApi.listItems({ search:search.value||undefined, category_id:filterCat.value||undefined, vectorization_status:filterVec.value||undefined, page:page.value, pageSize }); const d=r.data as any; items.value=d.items||[]; total.value=d.total||0 } catch(e:any){ error.value=e.message||'加载失败' } finally { loading.value=false }
}
let t:any=null; function debounceSearch(){clearTimeout(t);t=setTimeout(loadItems,300)}
function changePage(p:number){page.value=p;loadItems()}
function toggle(id:string){const i=selected.value.indexOf(id); i>=0?selected.value.splice(i,1):selected.value.push(id)}
function toggleAll(){allSelected.value?selected.value=[]:selected.value=items.value.map(i=>i.id)}
async function vecOne(id:string){try{await knowledgeBaseApi.revectorizeItem(id);await loadItems();successMsg.value='向量化完成'}catch(e:any){error.value=e.message}}
function confirmOne(it:KBItem){del.id=it.id;del.batch=false;del.msg=`确定删除「${(it.title||it.question).slice(0,40)}...」？对应向量也会被删除。`;del.visible=true}
function confirmBatchDel(){del.batch=true;del.msg=`确定删除选中的 ${selected.value.length} 条记录及对应向量？`;del.visible=true}
async function doDel(){del.visible=false; try{del.batch?await knowledgeBaseApi.batchDelete({item_ids:selected.value}):await knowledgeBaseApi.deleteItem(del.id);selected.value=[];successMsg.value='已删除';await loadItems()}catch(e:any){error.value=e.message}}
async function doBatchCat(){showCatDlg.value=false; try{await knowledgeBaseApi.batchUpdateCategory({item_ids:selected.value,category_id:batchCat.value||undefined as any});selected.value=[];successMsg.value='分类已更新';await loadItems()}catch(e:any){error.value=e.message}}
async function doBatchRevectorize(){
  // 过滤：只处理需要向量化的（未向量化或待重新向量化），已向量化的跳过
  const needVec = items.value.filter(it => selected.value.includes(it.id) && (it.needs_revectorize || !it.is_vectorized))
  if (needVec.length === 0) { successMsg.value = '选中的记录均已向量化，无需操作'; selected.value = []; return }
  try {
    const skipped = selected.value.length - needVec.length
    const r = await knowledgeBaseApi.batchRevectorize({item_ids: needVec.map(it => it.id)})
    successMsg.value = `完成: ${r.data.success} 成功` + (skipped > 0 ? `，${skipped} 条已向量化已跳过` : '')
    selected.value = []; await loadItems()
  } catch (e: any) { error.value = e.message }
}
function catName(cid?:string){return cid?categories.value.find(c=>c.id===cid)?.name||'—':'—'}
const diffMap:Record<string,string>={easy:'简单',medium:'中等',hard:'困难'}
function vecCls(it:KBItem){return it.needs_revectorize?'vec-pend':it.is_vectorized?'vec-ok':'vec-no'}
function vecLbl(it:KBItem){return it.needs_revectorize?'待重新向量化':it.is_vectorized?'已向量化':'未向量化'}
</script>
<style scoped>
.page-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.page-title{font-size:22px}
.header-actions{display:flex;gap:8px}
.btn-primary{padding:10px 20px;background:#1a73e8;color:#fff;border:none;border-radius:6px;text-decoration:none;font-size:14px;cursor:pointer}
.btn-outline{padding:10px 20px;background:#fff;color:#1a73e8;border:1px solid #1a73e8;border-radius:6px;text-decoration:none;font-size:14px}
.btn-outline:hover{background:#e8f0fe}
.filter-row{display:flex;gap:10px;margin-bottom:16px;align-items:center}
.filter-select{padding:8px 12px;border:1px solid #ddd;border-radius:6px;font-size:13px}
.batch-bar{display:flex;gap:10px;align-items:center;padding:10px 16px;background:#e8f0fe;border-radius:8px;margin-bottom:12px;font-size:13px}
.btn-sm{padding:6px 14px;font-size:12px;border:1px solid #d1d5db;border-radius:6px;background:#fff;cursor:pointer}
.btn-sm:hover{background:#f3f4f6}
.btn-danger{color:#dc2626;border-color:#fca5a5;background:#fef2f2}
.btn-danger:hover{background:#fee2e2}
.table-wrapper{background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,0.05)}
.kb-table{width:100%;border-collapse:collapse}
.kb-table th{padding:10px 12px;text-align:left;font-size:12px;font-weight:600;color:#6b7280;background:#f9fafb;border-bottom:1px solid #e5e7eb}
.kb-table td{padding:8px 12px;font-size:13px;color:#374151;border-bottom:1px solid #f3f4f6;vertical-align:middle}
.kb-table tbody tr:hover{background:#fafbfd}
.item-link{color:#1f2937;text-decoration:none;font-weight:600;line-height:1.4}
.item-link:hover{color:#4a90d9}
.item-sub{font-size:12px;color:#9ca3af;line-height:1.3;margin-top:2px;max-width:400px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tags-row{display:flex;gap:4px;margin-top:4px}
.mini-tag{font-size:10px;padding:1px 6px;background:#f3f4f6;border-radius:6px;color:#9ca3af}
.cell-muted{color:#9ca3af;font-size:12px}
.diff{font-size:11px;padding:2px 8px;border-radius:8px}
.diff.easy{background:#e8f5e9;color:#2e7d32}
.diff.medium{background:#fffbe6;color:#d48806}
.diff.hard{background:#fdecea;color:#c62828}
.vec-badge{font-size:11px;padding:2px 8px;border-radius:8px;font-weight:500}
.vec-ok{background:#e8f5e9;color:#2e7d32}
.vec-no{background:#fdecea;color:#c62828}
.vec-pend{background:#fff3e0;color:#e65100}
.cell-actions{display:flex;gap:2px;align-items:center}
.btn-act{font-size:12px;padding:2px 8px;border:1px solid #d1d5db;border-radius:4px;background:#fff;color:#374151;cursor:pointer;text-decoration:none;white-space:nowrap;line-height:1.4}
.btn-act:hover{background:#f3f4f6}
.btn-del{color:#dc2626;border-color:#fca5a5;background:#fef2f2}
.empty-row{text-align:center;color:#ccc;padding:40px}
.pagination{display:flex;justify-content:center;gap:12px;margin-top:16px;align-items:center}
.pagination button{padding:6px 14px;border:1px solid #ddd;border-radius:4px;background:#fff;cursor:pointer;font-size:13px}
.pagination button:disabled{opacity:0.4;cursor:not-allowed}
.success-banner{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background:#e8f5e9;color:#2e7d32;border-radius:8px;margin-bottom:14px;font-size:13px}
.success-banner button{background:none;border:none;color:#2e7d32;cursor:pointer}
.dialog-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;z-index:1000}
.dialog-box{background:#fff;border-radius:8px;padding:24px;min-width:360px;box-shadow:0 4px 20px rgba(0,0,0,0.15)}
.dialog-box h4{font-size:16px;margin-bottom:14px}
.form-input{width:100%;padding:8px 12px;border:1px solid #ddd;border-radius:4px;font-size:14px}
.dialog-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:16px}
.btn-secondary{padding:8px 16px;background:#f5f5f5;border:1px solid #ddd;border-radius:4px;cursor:pointer}
</style>
