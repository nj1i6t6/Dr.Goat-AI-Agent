<template>
  <div class="trace-public-page" v-loading="loading">
    <header class="public-header">
      <h1>產品產銷履歷</h1>
      <p class="subtitle">此頁面僅提供已公開的批次資訊，無需登入即可瀏覽。</p>
    </header>

    <el-empty
      v-if="!loading && errorMessage"
      :description="errorMessage"
    >
      <template #extra>
        <el-button type="primary" @click="retryFetch">重新嘗試</el-button>
      </template>
    </el-empty>

    <template v-else-if="story">
      <el-card class="batch-card" shadow="never">
        <template #header>
          <div class="card-header">
            <div>
              <h2 class="batch-title">{{ story.batch.product_name }}</h2>
              <p class="batch-number">批次號：{{ story.batch.batch_number }}</p>
            </div>
            <el-tag type="success" effect="dark" v-if="story.batch.is_public">對外公開中</el-tag>
          </div>
        </template>
        <div class="batch-meta">
          <div class="meta-item">
            <span class="label">產品類型</span>
            <span class="value">{{ story.batch.product_type || '未提供' }}</span>
          </div>
          <div class="meta-item">
            <span class="label">生產日期</span>
            <span class="value">{{ formatDate(story.batch.production_date) }}</span>
          </div>
          <div class="meta-item">
            <span class="label">建議賞味期限</span>
            <span class="value">{{ formatDate(story.batch.expiration_date) }}</span>
          </div>
        </div>
        <div class="batch-description" v-if="story.batch.description">
          <h4>產品簡介</h4>
          <p>{{ story.batch.description }}</p>
        </div>
        <div class="batch-description" v-if="story.batch.esg_highlights">
          <h4>ESG 亮點</h4>
          <el-alert :title="story.batch.esg_highlights" type="success" show-icon></el-alert>
        </div>
        <div class="batch-description" v-if="story.batch.origin_story">
          <h4>品牌故事</h4>
          <p>{{ story.batch.origin_story }}</p>
        </div>
      </el-card>

      <el-row :gutter="24" class="info-row">
        <el-col :md="12" :xs="24">
          <el-card shadow="never">
            <template #header>
              <div class="card-header">
                <h3>加工歷程</h3>
              </div>
            </template>
            <el-timeline>
              <el-timeline-item
                v-for="step in story.processing_timeline"
                :key="step.title + step.sequence_order"
                :timestamp="formatTimeline(step)"
                placement="top"
              >
                <div class="timeline-item">
                  <h4>{{ step.sequence_order ? `Step ${step.sequence_order}` : '步驟' }}</h4>
                  <p class="timeline-title">{{ step.title }}</p>
                  <p class="timeline-desc" v-if="step.description">{{ step.description }}</p>
                  <el-link v-if="step.evidence_url" :href="step.evidence_url" target="_blank" type="primary">
                    查看佐證資料
                  </el-link>
                </div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-if="!story.processing_timeline.length" description="尚未建立加工流程" />
          </el-card>
        </el-col>
        <el-col :md="12" :xs="24">
          <el-card shadow="never">
            <template #header>
              <div class="card-header">
                <h3>參與羊隻</h3>
              </div>
            </template>
            <el-empty v-if="!story.sheep_details.length" description="尚未關聯羊隻" />
            <el-collapse v-else accordion>
              <el-collapse-item
                v-for="detail in story.sheep_details"
                :key="detail.link.id"
                :title="formatSheepTitle(detail)"
              >
                <div class="sheep-section">
                  <h4>基本資料</h4>
                  <div class="grid">
                    <div class="grid-item"><span>耳號</span><strong>{{ detail.sheep.EarNum }}</strong></div>
                    <div class="grid-item"><span>品種</span><strong>{{ detail.sheep.Breed || '未提供' }}</strong></div>
                    <div class="grid-item"><span>性別</span><strong>{{ detail.sheep.Sex || '未提供' }}</strong></div>
                    <div class="grid-item"><span>牧場編號</span><strong>{{ detail.sheep.FarmNum || '未提供' }}</strong></div>
                  </div>
                  <div class="section-block" v-if="detail.link.notes">
                    <h5>角色備註</h5>
                    <p>{{ detail.link.notes }}</p>
                  </div>
                  <div class="section-block" v-if="detail.recent_events.length">
                    <h5>重要事件</h5>
                    <ul class="bullet-list">
                      <li v-for="event in detail.recent_events" :key="event.id">
                        <strong>{{ event.event_date }}</strong>｜{{ event.event_type }}
                        <span v-if="event.description"> - {{ event.description }}</span>
                        <el-tag v-if="event.medication" type="warning" size="small">用藥：{{ event.medication }}</el-tag>
                      </li>
                    </ul>
                  </div>
                  <div class="section-block" v-if="detail.recent_history.length">
                    <h5>歷史數據</h5>
                    <ul class="bullet-list">
                      <li v-for="record in detail.recent_history" :key="record.id">
                        {{ record.record_date }}｜{{ record.record_type }}：{{ record.value }}
                        <span v-if="record.notes">（{{ record.notes }}）</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </el-collapse-item>
            </el-collapse>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import api from '../api';

const route = useRoute();
const batchNumber = computed(() => route.params.batchNumber);
const loading = ref(false);
const story = ref(null);
const errorMessage = ref('');

const fetchStory = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    story.value = await api.getPublicTraceBatch(batchNumber.value);
  } catch (error) {
    errorMessage.value = error?.error || error?.message || '載入產銷履歷失敗';
    ElMessage.error(errorMessage.value);
  } finally {
    loading.value = false;
  }
};

const retryFetch = () => fetchStory();

const formatDate = (value) => {
  if (!value) return '未提供';
  try {
    return new Date(value).toLocaleDateString();
  } catch (error) {
    return value;
  }
};

const formatTimeline = (step) => {
  const started = step.started_at ? new Date(step.started_at).toLocaleString() : null;
  const completed = step.completed_at ? new Date(step.completed_at).toLocaleString() : null;
  if (started && completed) {
    return `${started} ~ ${completed}`;
  }
  return started || completed || '';
};

const formatSheepTitle = (detail) => {
  const sheep = detail.sheep || {};
  const roleText = detail.link.role || detail.link.contribution_type || '參與';
  return `${sheep.EarNum || '未知耳號'}｜${roleText}`;
};

onMounted(fetchStory);
</script>

<style scoped>
.trace-public-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 30px 20px 60px;
  min-height: 100vh;
}

.public-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.public-header h1 {
  margin: 0;
  font-size: 2rem;
  color: #1f2937;
  font-weight: 700;
}

.public-header .subtitle {
  margin: 0;
  color: #64748b;
}

.batch-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.batch-title {
  margin: 0;
  font-size: 1.8rem;
  color: #1e3a8a;
}

.batch-number {
  margin: 4px 0 0;
  color: #64748b;
}

.batch-meta {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.meta-item {
  background: #f8fafc;
  border-radius: 12px;
  padding: 12px;
}

.meta-item .label {
  display: block;
  color: #64748b;
  font-size: 0.85rem;
}

.meta-item .value {
  font-weight: 600;
  color: #1f2937;
}

.batch-description {
  margin-top: 20px;
}

.batch-description h4 {
  margin-bottom: 8px;
  color: #1e293b;
}

.info-row {
  margin-top: 30px;
}

.timeline-item {
  padding-bottom: 12px;
}

.timeline-title {
  font-size: 1.1rem;
  color: #0f172a;
  margin: 4px 0;
}

.timeline-desc {
  color: #4b5563;
}

.sheep-section {
  padding: 10px 4px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
  margin-bottom: 15px;
}

.grid-item {
  background: #f1f5f9;
  border-radius: 10px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.grid-item span {
  font-size: 0.75rem;
  color: #64748b;
}

.grid-item strong {
  color: #0f172a;
}

.section-block {
  margin-bottom: 18px;
}

.section-block h5 {
  margin-bottom: 6px;
  color: #1e3a8a;
}

.bullet-list {
  margin: 0;
  padding-left: 18px;
  color: #334155;
}

.bullet-list li {
  margin-bottom: 6px;
}

@media (max-width: 768px) {
  .trace-public-page {
    padding: 20px 12px 40px;
  }

  .batch-title {
    font-size: 1.5rem;
  }

  .info-row {
    margin-top: 20px;
  }
}
</style>
