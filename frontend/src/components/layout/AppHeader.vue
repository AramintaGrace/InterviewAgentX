<template>
  <header class="app-header">
    <div class="header-left">
      <h1 class="logo">🎯 InterviewAgentX</h1>
      <span class="subtitle">智能面试辅助系统</span>
    </div>
    <div class="header-right">
      <nav class="breadcrumb">
        <router-link to="/">首页</router-link>
        <span class="separator">/</span>
        <span class="current">{{ currentTitle }}</span>
      </nav>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const currentTitle = computed(() => route.meta?.title || '页面')
</script>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
}

.subtitle {
  font-size: 13px;
  color: #999;
}

.header-right {
  display: flex;
  align-items: center;
}

.breadcrumb {
  font-size: 14px;
  color: #666;
}

.breadcrumb a {
  color: #4a90d9;
  text-decoration: none;
}

.breadcrumb a:hover {
  text-decoration: underline;
}

.separator {
  margin: 0 8px;
  color: #ccc;
}

.current {
  color: #333;
}
</style>
