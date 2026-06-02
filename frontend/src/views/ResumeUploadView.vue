<template>
  <div class="resume-upload">
    <h2 class="page-title">📄 上传简历</h2>
    <ResumeUploader @uploaded="onUploaded" />
    <ResumeInfoCard v-if="resume" :resume="resume" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ResumeUploader from '@/components/resume/ResumeUploader.vue'
import ResumeInfoCard from '@/components/resume/ResumeInfoCard.vue'

const resume = ref(null)

function onUploaded(data: any) {
  resume.value = data
}
</script>

<style scoped>
.page-title {
  font-size: 22px;
  margin-bottom: 24px;
}
</style>
