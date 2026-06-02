<template>
  <div class="dossier-page">
    <router-link to="/records" class="back-link">← 返回记录列表</router-link>

    <ErrorBanner v-if="error" :message="error" @dismiss="error = ''" />
    <LoadingSpinner v-if="loading" text="加载候选人档案..." />

    <template v-if="dossier">
      <!-- ===== 候选人基本信息 ===== -->
      <div class="candidate-hero">
        <div class="hero-avatar">{{ dossier.candidate.name.charAt(0) }}</div>
        <div class="hero-info">
          <h2>{{ dossier.candidate.name }}</h2>
          <div class="hero-meta">
            <span v-if="dossier.candidate.current_role">💼 {{ dossier.candidate.current_role }}</span>
            <span v-if="dossier.candidate.email">📧 {{ dossier.candidate.email }}</span>
            <span v-if="dossier.candidate.phone">📱 {{ dossier.candidate.phone }}</span>
            <span v-if="dossier.candidate.years_of_exp != null">📅 {{ dossier.candidate.years_of_exp }}年经验</span>
          </div>
        </div>
      </div>

      <!-- ===== 简历 ===== -->
      <div class="section" v-if="dossier.resumes.length">
        <h3>📄 简历 ({{ dossier.resumes.length }})</h3>

        <div class="resume-list">
          <div v-for="(r, ri) in dossier.resumes" :key="r.id" class="resume-card">
            <div class="resume-file">
              <div class="resume-file-header">
                <span class="file-name">{{ r.file_name }}</span>
                <span class="file-meta">{{ formatSize(r.file_size_bytes) }} · {{ r.ocr_status === 'completed' ? '✅ 已识别' : r.ocr_status }}</span>
              </div>

              <!-- 简历图片预览 -->
              <div v-if="r.file_url" class="resume-preview">
                <button
                  v-if="isImage(r.mime_type) && !imgSrcs[ri]"
                  class="btn-load-preview"
                  :disabled="imgLoading[ri]"
                  @click="loadResumeImage(ri, r)"
                >
                  {{ imgLoading[ri] ? '⏳ 加载中...' : '🖼️ 查看简历图片' }}
                </button>
                <img
                  v-if="imgSrcs[ri]"
                  :src="imgSrcs[ri]"
                  class="resume-img"
                  @click="openImage(imgSrcs[ri])"
                />
                <a v-if="!isImage(r.mime_type)" :href="r.file_url" target="_blank" class="btn-download">📥 下载简历文件</a>
              </div>

              <!-- OCR 错误 -->
              <div v-if="r.ocr_status === 'failed'" class="ocr-error">
                ⚠️ OCR 失败: {{ r.ocr_error_msg || '未知错误' }}
              </div>

              <!-- 解析的简历信息 -->
              <div v-if="r.parsed_data" class="parsed-section">
                <h5>📋 解析信息</h5>
                <div class="parsed-grid">
                  <div v-if="r.parsed_data.name"><label>姓名</label><span>{{ r.parsed_data.name }}</span></div>
                  <div v-if="r.parsed_data.email"><label>邮箱</label><span>{{ r.parsed_data.email }}</span></div>
                  <div v-if="r.parsed_data.phone"><label>电话</label><span>{{ r.parsed_data.phone }}</span></div>
                </div>
                <div v-if="r.parsed_data.skills?.length" class="skill-tags">
                  <span v-for="sk in r.parsed_data.skills" :key="sk" class="skill-tag">{{ sk }}</span>
                </div>
              </div>

              <!-- 简历 AI 分析 -->
              <div v-if="r.analysis" class="analysis-box">
                <h5 @click="toggleAnalysis(ri)" class="toggle-title">
                  🤖 AI 简历分析 {{ showAnalysis[ri] ? '▲' : '▼' }}
                </h5>
                <div v-if="showAnalysis[ri]">
                  <p v-if="r.analysis.analysis_json?.overall_assessment" class="ana-text">
                    {{ r.analysis.analysis_json.overall_assessment }}
                  </p>
                  <div v-if="r.analysis.analysis_json?.strengths?.length" class="tag-section">
                    <h6>✅ 优势</h6>
                    <div class="tags">
                      <span v-for="s in r.analysis.analysis_json.strengths" :key="s" class="tag tag-good">{{ s }}</span>
                    </div>
                  </div>
                  <div v-if="r.analysis.analysis_json?.weaknesses?.length" class="tag-section">
                    <h6>⚠️ 待提升</h6>
                    <div class="tags">
                      <span v-for="w in r.analysis.analysis_json.weaknesses" :key="w" class="tag tag-warn">{{ w }}</span>
                    </div>
                  </div>
                  <div v-if="r.analysis.analysis_json?.skill_match" class="skill-scores">
                    <h6>🛠 技能评分</h6>
                    <div v-for="(score, skill) in r.analysis.analysis_json.skill_match" :key="skill" class="score-row">
                      <span class="skill-name">{{ skill }}</span>
                      <div class="skill-bar"><div class="skill-fill" :style="{width:((score)/10*100)+'%'}"></div></div>
                      <span class="skill-val">{{ score }}/10</span>
                    </div>
                  </div>
                  <div v-if="r.analysis.analysis_json?.experience_relevance_score" class="tag-row">
                    <span class="tag-good">经验相关度: {{ r.analysis.analysis_json.experience_relevance_score }}/100</span>
                  </div>
                  <div v-if="r.analysis.analysis_json?.project_highlights?.length" class="ana-projects">
                    <h6>🚀 项目亮点</h6>
                    <div v-for="(p, i) in r.analysis.analysis_json.project_highlights" :key="i" class="project-item">
                      <span class="project-name">{{ p.project }}</span>
                      <p class="project-desc">{{ p.depth_analysis }}</p>
                    </div>
                  </div>
                  <div v-if="r.analysis.analysis_json?.suggested_questions?.length" class="ana-questions">
                    <h6>💬 建议面试题目</h6>
                    <ol><li v-for="(q,i) in r.analysis.analysis_json.suggested_questions" :key="i">{{ q }}</li></ol>
                  </div>
                  <div v-if="r.analysis.analysis_json?.red_flags?.length" class="tag-section">
                    <h6>🔴 风险提示</h6>
                    <div class="tags">
                      <span v-for="f in r.analysis.analysis_json.red_flags" :key="f" class="tag tag-red">{{ f }}</span>
                    </div>
                  </div>
                  <div class="ana-meta">
                    <span>🤖 {{ r.analysis.agent_model }}</span>
                    <span v-if="r.analysis.tokens_used">🪙 {{ r.analysis.tokens_used }} tokens</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 面试历史 ===== -->
      <div class="section" v-if="dossier.interviews.length">
        <h3>🎤 面试记录 ({{ dossier.interviews.length }})</h3>

        <div class="interview-list">
          <div v-for="(inv, ii) in dossier.interviews" :key="inv.session_id" class="interview-card">
            <div class="inv-header">
              <span class="inv-status" :class="inv.status">{{ statusLabel(inv.status) }}</span>
              <span class="inv-questions">{{ inv.completed_questions }}/{{ inv.total_questions }} 题</span>
              <span v-if="inv.total_score != null" class="inv-score" :class="scoreColor(inv.total_score)">{{ inv.total_score }} 分</span>
              <span class="inv-date">{{ inv.created_at?.split('T')[0] }}</span>
            </div>

            <!-- 面试报告 -->
            <div v-if="inv.report" class="report-box">
              <h5 @click="toggleReport(ii)" class="toggle-title">
                📊 面试报告 {{ showReport[ii] ? '▲' : '▼' }}
              </h5>
              <div v-if="showReport[ii] && inv.report.report_json">
                <div class="report-summary-row">
                  <div class="report-stat">
                    <span class="rs-value" :class="scoreColor(inv.report.report_json.overall_score)">
                      {{ inv.report.report_json.overall_score }}
                    </span>
                    <span class="rs-label">综合评分</span>
                  </div>
                </div>

                <div v-if="inv.report.report_json.dimension_scores" class="dim-bars">
                  <div v-for="(score, dim) in inv.report.report_json.dimension_scores" :key="dim" class="dim-row">
                    <span class="dim-name">{{ dimLabel(dim) }}</span>
                    <div class="dim-track"><div class="dim-fill" :class="barColor(score)" :style="{ width: (score ?? 0) + '%' }"></div></div>
                    <span class="dim-val">{{ score ?? '—' }}</span>
                  </div>
                </div>

                <p v-if="inv.report.report_json.detailed_feedback" class="report-feedback">
                  {{ inv.report.report_json.detailed_feedback }}
                </p>

                <div v-if="inv.report.report_json.question_reviews?.length" class="qr-section">
                  <h6>逐题回顾</h6>
                  <div v-for="(qr, i) in inv.report.report_json.question_reviews" :key="i" class="qr-row">
                    <span class="qr-num">{{ i+1 }}.</span>
                    <span class="qr-text">{{ qr.question_text }}</span>
                    <span class="qr-score">{{ qr.score }}分</span>
                  </div>
                </div>

                <div class="ana-meta">
                  <span>🤖 {{ inv.report.agent_model }}</span>
                  <span v-if="inv.report.tokens_used">🪙 {{ inv.report.tokens_used }} tokens</span>
                </div>
              </div>
            </div>
            <div v-else class="no-report">暂无报告</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorBanner from '@/components/common/ErrorBanner.vue'
import { recordsApi } from '@/api/reports'
import { resumesApi } from '@/api/resumes'

const route = useRoute()
const dossier = ref<any>(null)
const loading = ref(true)
const error = ref('')

// 独立的响应式状态，不用 reactive 加属性到 API 数据上
const showAnalysis = reactive<Record<number, boolean>>({})
const showReport = reactive<Record<number, boolean>>({})
const imgSrcs = reactive<Record<number, string | null>>({})
const imgLoading = reactive<Record<number, boolean>>({})

onMounted(async () => {
  const cid = route.params.candidateId as string
  loading.value = true
  try {
    const res = await recordsApi.getDossier(cid)
    dossier.value = res.data
  } catch (e: any) {
    error.value = e.message || '加载候选人档案失败'
  } finally { loading.value = false }
})

function toggleAnalysis(idx: number) {
  showAnalysis[idx] = !showAnalysis[idx]
}

function toggleReport(idx: number) {
  showReport[idx] = !showReport[idx]
}

function openImage(url: string) { window.open(url, '_blank') }
function isImage(mime: string) { return /^image\//.test(mime) }

function formatSize(bytes: number) {
  if (!bytes) return '0 B'
  const u = ['B','KB','MB','GB']; const i = Math.floor(Math.log(bytes)/Math.log(1024))
  return (bytes/Math.pow(1024,i)).toFixed(i>0?1:0)+' '+u[i]
}

async function loadResumeImage(idx: number, r: any) {
  imgLoading[idx] = true
  try {
    const res = await resumesApi.getResumeFileUrl(r.id)
    const url = res.data.url
    imgSrcs[idx] = url.startsWith('http') ? url : r.file_url
  } catch {
    imgSrcs[idx] = r.file_url
  } finally {
    imgLoading[idx] = false
  }
}

function statusLabel(s: string) {
  const m: Record<string,string> = { created:'已创建', in_progress:'进行中', paused:'暂停', completed:'已完成', cancelled:'已取消' }
  return m[s] || s
}
function scoreColor(s?: number) {
  if (s==null) return ''; if (s>=80) return 'green'; if (s>=60) return 'yellow'; return 'red'
}
function barColor(s: number|null) {
  if (s==null) return ''; if (s>=80) return 'bar-high'; if (s>=60) return 'bar-mid'; return 'bar-low'
}
const dimMap: Record<string,string> = {
  technical_ability:'技术能力', communication:'沟通表达', problem_solving:'问题解决',
  experience_relevance:'经验匹配', cultural_fit:'文化契合',
}
function dimLabel(k: string) { return dimMap[k] || k }
</script>

<style scoped>
.back-link { display: inline-block; margin-bottom: 16px; color: #4a90d9; text-decoration: none; font-size: 14px; }
.back-link:hover { text-decoration: underline; }

.candidate-hero { display: flex; gap: 20px; align-items: center; background: #fff; border-radius: 12px; padding: 28px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 20px; }
.hero-avatar { width: 64px; height: 64px; border-radius: 50%; background: linear-gradient(135deg,#6366f1,#8b5cf6); color: #fff; font-size: 28px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.hero-info h2 { font-size: 22px; font-weight: 700; margin-bottom: 8px; }
.hero-meta { display: flex; gap: 16px; flex-wrap: wrap; font-size: 13px; color: #6b7280; }

.section { margin-bottom: 24px; }
.section h3 { font-size: 18px; font-weight: 700; margin-bottom: 14px; }

.resume-card { background: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 12px; }
.resume-file-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.file-name { font-weight: 600; font-size: 14px; }
.file-meta { font-size: 12px; color: #999; }
.resume-preview { margin-bottom: 12px; }
.resume-img { max-width: 100%; max-height: 300px; border-radius: 6px; border: 1px solid #eee; cursor: zoom-in; object-fit: contain; }
.btn-load-preview { padding: 8px 16px; background: #e8f0fe; color: #1a73e8; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
.btn-load-preview:hover:not(:disabled) { background: #d2e3fc; }
.btn-load-preview:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-download { display: inline-block; padding: 6px 14px; background: #e8f0fe; color: #1a73e8; border-radius: 6px; text-decoration: none; font-size: 13px; }
.ocr-error { font-size: 13px; color: #c62828; padding: 8px 12px; background: #fdecea; border-radius: 6px; margin-bottom: 10px; }

.parsed-section { margin-bottom: 12px; }
.parsed-section h5 { font-size: 13px; color: #666; margin-bottom: 6px; }
.parsed-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 8px; }
.parsed-grid div label { font-size: 11px; color: #999; display: block; }
.parsed-grid div span { font-size: 13px; color: #333; }
.skill-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.skill-tag { font-size: 11px; padding: 2px 8px; background: #e8f0fe; color: #1a73e8; border-radius: 8px; }

.analysis-box, .report-box { border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px 16px; margin-top: 10px; }
.toggle-title { font-size: 14px; font-weight: 600; cursor: pointer; user-select: none; margin-bottom: 8px; color: #374151; }
.toggle-title:hover { color: #4a90d9; }
.ana-text { font-size: 13px; color: #4b5563; line-height: 1.6; margin-bottom: 8px; }
.tag-section { margin: 10px 0; }
.tag-section h6 { font-size: 12px; color: #666; margin-bottom: 4px; }
.tag-row { margin-bottom: 6px; }
.tag-good { font-size: 12px; color: #2e7d32; background: #e8f5e9; padding: 3px 8px; border-radius: 6px; }
.tag-warn { font-size: 12px; color: #e65100; background: #fff3e0; padding: 3px 8px; border-radius: 6px; }
.tag-red { font-size: 12px; color: #c62828; background: #fdecea; padding: 3px 8px; border-radius: 6px; }
.ana-questions { margin-bottom: 8px; }
.ana-questions h6 { font-size: 12px; color: #666; margin-bottom: 4px; }
.ana-questions ol { padding-left: 20px; font-size: 13px; color: #4b5563; line-height: 1.8; }
.ana-meta { display: flex; gap: 12px; font-size: 11px; color: #999; margin-top: 8px; }

.interview-card { background: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 12px; }
.inv-header { display: flex; align-items: center; gap: 14px; margin-bottom: 12px; flex-wrap: wrap; }
.inv-status { font-size: 12px; padding: 2px 10px; border-radius: 8px; }
.inv-status.completed { background: #e8f5e9; color: #2e7d32; }
.inv-status.in_progress { background: #e3f2fd; color: #1565c0; }
.inv-questions { font-size: 13px; color: #666; }
.inv-score { font-size: 18px; font-weight: 700; }
.inv-score.green { color: #22c55e; } .inv-score.yellow { color: #eab308; } .inv-score.red { color: #ef4444; }
.inv-date { font-size: 12px; color: #999; margin-left: auto; }
.no-report { font-size: 13px; color: #999; }

.report-summary-row { display: flex; gap: 20px; align-items: center; margin-bottom: 12px; }
.report-stat { display: flex; flex-direction: column; align-items: center; }
.rs-value { font-size: 28px; font-weight: 700; }
.rs-value.green { color: #22c55e; } .rs-value.yellow { color: #eab308; } .rs-value.red { color: #ef4444; }
.rs-label { font-size: 11px; color: #999; }
.dim-bars { margin-bottom: 12px; }
.dim-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.dim-name { width: 80px; font-size: 12px; color: #666; text-align: right; }
.dim-track { flex: 1; height: 6px; background: #e5e7eb; border-radius: 3px; overflow: hidden; }
.dim-fill { height: 100%; border-radius: 3px; transition: width 0.4s; background: #6366f1; }
.bar-high { background: #22c55e; } .bar-mid { background: #eab308; } .bar-low { background: #ef4444; }
.dim-val { width: 28px; font-size: 12px; font-weight: 600; color: #333; text-align: center; }

.report-feedback { font-size: 13px; color: #4b5563; line-height: 1.6; margin-bottom: 10px; }

.qr-section { margin: 10px 0; }
.qr-section h6 { font-size: 12px; color: #666; margin-bottom: 6px; }
.qr-row { display: flex; gap: 8px; align-items: baseline; font-size: 13px; color: #4b5563; padding: 4px 0; border-bottom: 1px solid #f9fafb; }
.qr-num { color: #999; min-width: 20px; }
.qr-text { flex: 1; }
.qr-score { font-weight: 600; color: #6366f1; white-space: nowrap; }

.skill-scores { margin: 8px 0; }
.skill-scores h6 { font-size: 12px; color: #666; margin-bottom: 4px; }
.score-row { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.skill-name { width: 100px; font-size: 11px; color: #666; text-align: right; }
.skill-bar { flex: 1; height: 5px; background: #e5e7eb; border-radius: 3px; overflow: hidden; }
.skill-fill { height: 100%; background: #6366f1; border-radius: 3px; }
.skill-val { font-size: 11px; color: #6366f1; font-weight: 600; min-width: 30px; }

.ana-projects { margin: 8px 0; }
.ana-projects h6 { font-size: 12px; color: #666; margin-bottom: 4px; }
.project-item { margin-bottom: 6px; }
.project-name { font-size: 13px; font-weight: 600; color: #374151; }
.project-desc { font-size: 12px; color: #6b7280; margin: 2px 0 0 0; line-height: 1.5; }

.tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag { font-size: 12px; padding: 3px 10px; border-radius: 8px; }
</style>
