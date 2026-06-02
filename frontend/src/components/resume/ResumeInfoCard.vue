<template>
  <div class="resume-info-card" v-if="resume">
    <h3>简历信息</h3>
    <div class="info-grid">
      <div class="info-item"><label>姓名</label><span>{{ resume.name || '-' }}</span></div>
      <div class="info-item"><label>邮箱</label><span>{{ resume.email || '-' }}</span></div>
      <div class="info-item"><label>电话</label><span>{{ resume.phone || '-' }}</span></div>
      <div class="info-item"><label>当前职位</label><span>{{ resume.currentRole || '-' }}</span></div>
    </div>
    <div v-if="resume.skills?.length" class="skills-section">
      <h4>技能</h4>
      <div class="skill-tags">
        <span v-for="skill in resume.skills" :key="skill" class="skill-tag">{{ skill }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ resume: any }>()
</script>

<style scoped>
.resume-info-card { background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-top: 24px; }
h3 { font-size: 16px; margin-bottom: 16px; }
h4 { font-size: 14px; margin: 16px 0 8px; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.info-item label { display: block; font-size: 12px; color: #999; }
.info-item span { font-size: 14px; color: #333; }
.skill-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.skill-tag { background: #e8f0fe; color: #1a73e8; padding: 4px 10px; border-radius: 12px; font-size: 13px; }
</style>
