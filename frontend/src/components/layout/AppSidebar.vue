<template>
  <aside class="app-sidebar">
    <nav class="sidebar-nav">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item) }"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

const menuItems = [
  { path: '/', label: '首页', icon: '📊' },
  { path: '/resumes/upload', label: '简历分析', icon: '📄' },
  { path: '/interviews/create', label: '面试作答', icon: '🎤' },
  { path: '/knowledge-base', label: '知识库', icon: '📚' },
  { path: '/records', label: '面试记录', icon: '📋' },
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
  min-height: calc(100vh - 56px);
  padding-top: 8px;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  color: #bbb;
  text-decoration: none;
  transition: all 0.2s;
  font-size: 14px;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.nav-item.active {
  background: rgba(74, 144, 217, 0.25);
  color: #fff;
  border-right: 3px solid #4a90d9;
}

.nav-icon {
  font-size: 18px;
}

.nav-label {
  font-size: 14px;
}
</style>
