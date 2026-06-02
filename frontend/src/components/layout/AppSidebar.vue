<template>
  <aside class="app-sidebar">
    <!-- 系统名称 -->
    <div class="sidebar-brand">
      <h1 class="brand-title">InterviewAgentX</h1>
      <span class="brand-subtitle">智能面试辅助系统</span>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item) }"
      >
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

const menuItems = [
  { path: '/', label: '首页' },
  { path: '/resumes/upload', label: '简历分析' },
  { path: '/interviews/create', label: '面试作答' },
  { path: '/records', label: '面试记录' },
  { path: '/knowledge-base', label: '知识库' },
]

function isActive(item: { path: string }): boolean {
  if (item.path === '/') return route.path === '/'
  return route.path.startsWith(item.path.split('/')[1] ? `/${item.path.split('/')[1]}` : item.path)
}
</script>

<style scoped>
.app-sidebar {
  width: 200px;
  background: #1a1a2e;
  color: #fff;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.sidebar-brand {
  padding: 24px 20px 28px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand-title {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
}

.brand-subtitle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
  display: block;
  margin-top: 4px;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-top: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 14px 24px;
  color: #a0aec0;
  text-decoration: none;
  transition: all 0.2s;
  font-size: 14px;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
}

.nav-item.active {
  background: rgba(99, 102, 241, 0.25);
  color: #fff;
  border-right: 3px solid #6366f1;
  font-weight: 600;
}

.nav-label {
  font-size: 14px;
}
</style>
