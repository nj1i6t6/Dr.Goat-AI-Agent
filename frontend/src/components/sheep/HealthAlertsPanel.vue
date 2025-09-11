<template>
  <div class="health-alerts">
    <el-empty v-if="alerts.length === 0" description="羊群健康狀況良好" />
    <el-timeline v-else>
      <el-timeline-item
        v-for="a in alerts"
        :key="a.id"
        :timestamp="a.record_date || a.created_at"
        :type="a.status === 'resolved' ? 'success' : 'danger'"
      >
        <div class="alert-item">
          <div class="header">
            <strong>{{ a.alert_type }}</strong>
            <el-tag size="small" :type="a.status === 'resolved' ? 'success' : 'danger'">
              {{ a.status === 'resolved' ? '已處理' : '待處理' }}
            </el-tag>
          </div>
          <div class="meta">耳號 {{ a.ear_num }} · 偏離 {{ a.deviation_pct }}% · 預測 {{ a.predicted_weight }}kg · 實測 {{ a.actual_weight }}kg</div>
          <div class="message" v-html="a.message"></div>
          <div class="actions">
            <el-button size="small" @click="$emit('view', a)">查看詳情</el-button>
            <el-button size="small" type="success" plain :disabled="a.status==='resolved'" @click="$emit('resolve', a)">我已處理</el-button>
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup>
defineProps({ alerts: { type: Array, default: () => [] } });
defineEmits(['resolve','view']);
</script>

<style scoped>
.alert-item { display:flex; flex-direction: column; gap:6px; }
.header { display:flex; gap:8px; align-items:center; }
.meta { color:#6b7280; font-size: 12px; }
.message { margin-top: 4px; }
.actions { margin-top: 6px; display:flex; gap:6px; }
</style>
