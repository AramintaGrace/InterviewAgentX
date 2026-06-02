import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { KBCategory, KBItem, KBItemCreate, KBItemUpdate } from '@/types/knowledgeBase'
import { knowledgeBaseApi } from '@/api/knowledgeBase'

export const useKnowledgeBaseStore = defineStore('knowledgeBase', () => {
  const categories = ref<KBCategory[]>([])
  const items = ref<KBItem[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function loadCategories() {
    try {
      const response = await knowledgeBaseApi.listCategories()
      categories.value = response.data
    } catch (e: any) {
      error.value = e.message || '加载分类失败'
    }
  }

  async function createCategory(name: string, parentId?: string) {
    try {
      const res = await knowledgeBaseApi.createCategory({ name, parent_id: parentId })
      categories.value.push(res.data)
      return res.data
    } catch (e: any) {
      error.value = e.message || '创建分类失败'
      throw e
    }
  }

  async function loadItems(params?: {
    categoryId?: string; search?: string; tag?: string;
    difficulty?: string; page?: number; pageSize?: number
  }) {
    loading.value = true
    error.value = null
    try {
      const response = await knowledgeBaseApi.listItems(params)
      const data = response.data as any
      if (data.items) {
        items.value = data.items
        total.value = data.total
      } else {
        items.value = Array.isArray(data) ? data : []
        total.value = items.value.length
      }
    } catch (e: any) {
      error.value = e.message || '加载知识库失败'
    } finally {
      loading.value = false
    }
  }

  async function createItem(data: KBItemCreate) {
    loading.value = true
    error.value = null
    try {
      const response = await knowledgeBaseApi.createItem(data)
      items.value.unshift(response.data)
      total.value++
      return response.data
    } catch (e: any) {
      error.value = e.message || '创建失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateItem(id: string, data: KBItemUpdate) {
    loading.value = true
    error.value = null
    try {
      const response = await knowledgeBaseApi.updateItem(id, data)
      const idx = items.value.findIndex(i => i.id === id)
      if (idx !== -1) items.value[idx] = response.data
      return response.data
    } catch (e: any) {
      error.value = e.message || '更新失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteItem(id: string) {
    error.value = null
    try {
      await knowledgeBaseApi.deleteItem(id)
      items.value = items.value.filter(i => i.id !== id)
      total.value--
    } catch (e: any) {
      error.value = e.message || '删除失败'
      throw e
    }
  }

  function reset() {
    categories.value = []
    items.value = []
    total.value = 0
    loading.value = false
    error.value = null
  }

  return {
    categories, items, total, loading, error,
    loadCategories, createCategory,
    loadItems, createItem, updateItem, deleteItem, reset,
  }
})
