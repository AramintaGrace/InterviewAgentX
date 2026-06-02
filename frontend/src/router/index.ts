import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { title: '首页', icon: 'dashboard' },
  },
  // Resume
  {
    path: '/resumes/upload',
    name: 'ResumeUpload',
    component: () => import('@/views/ResumeUploadView.vue'),
    meta: { title: '上传简历', icon: 'upload' },
  },
  {
    path: '/resumes/:resumeId/analysis',
    name: 'ResumeAnalysis',
    component: () => import('@/views/ResumeAnalysisView.vue'),
    meta: { title: '简历分析' },
  },
  // Interview
  {
    path: '/interviews/create',
    name: 'InterviewCreate',
    component: () => import('@/views/InterviewCreateView.vue'),
    meta: { title: '创建面试' },
  },
  {
    path: '/interviews/:sessionId',
    name: 'InterviewSession',
    component: () => import('@/views/InterviewSessionView.vue'),
    meta: { title: '面试作答' },
  },
  // Report
  {
    path: '/reports/:sessionId',
    name: 'InterviewReport',
    component: () => import('@/views/InterviewReportView.vue'),
    meta: { title: '面试报告', icon: 'bar-chart' },
  },
  // Knowledge Base
  {
    path: '/knowledge-base',
    name: 'KnowledgeBase',
    component: () => import('@/views/KnowledgeBaseView.vue'),
    meta: { title: '知识库', icon: 'book' },
  },
  {
    path: '/knowledge-base/create',
    name: 'KnowledgeBaseCreate',
    component: () => import('@/views/KnowledgeBaseEditView.vue'),
    meta: { title: '添加问答' },
  },
  {
    path: '/knowledge-base/:itemId/edit',
    name: 'KnowledgeBaseEdit',
    component: () => import('@/views/KnowledgeBaseEditView.vue'),
    meta: { title: '编辑问答' },
    props: true,
  },
  // Records
  {
    path: '/records',
    name: 'InterviewRecords',
    component: () => import('@/views/InterviewRecordsView.vue'),
    meta: { title: '面试记录', icon: 'archive' },
  },
  {
    path: '/records/:candidateId',
    name: 'RecordDetail',
    component: () => import('@/views/InterviewRecordDetailView.vue'),
    meta: { title: '记录详情' },
  },
  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: '页面不存在' },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to, from) => {
  if (from.name === 'InterviewSession' && to.name !== 'InterviewSession') {
    // Could add a confirmation dialog here
  }
})

export default router
