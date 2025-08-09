<template>
  <el-dialog
    v-model="dialogVisible"
    :title="currentStep.title"
    width="500px"
    :before-close="handleClose"
    :close-on-click-modal="false"
    append-to-body
  >
    <div class="guide-content" v-html="currentStep.content"></div>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">跳過教學</el-button>
        <div>
          <el-button @click="prevStep" :disabled="currentStepIndex === 0">上一步</el-button>
          <el-button type="primary" @click="nextStep">
            {{ isLastStep ? '完成教學' : '下一步' }}
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:visible']);

const dialogVisible = ref(props.visible);
const currentStepIndex = ref(0);

const steps = [
  {
    title: '歡迎來到領頭羊博士！',
    content: '這是一個快速的導覽，將帶您了解系統的核心功能。'
  },
  {
    title: '第一步：導入資料',
    content: '首先，您需要將您的羊隻資料導入系統。請前往「數據管理」頁面，下載我們的標準範本，填寫後上傳即可。'
  },
  {
    title: '第二步：設定 API 金鑰',
    content: '為了使用 AI 相關功能，如智慧諮詢和生長預測分析，您需要在「系統設定」頁面中設定您的 Google Gemini API 金鑰。'
  },
  {
    title: '第三步：查看羊群總覽',
    content: '在「羊群總覽」頁面，您可以查看、篩選和管理所有羊隻的詳細資料。'
  },
  {
    title: '第四步：生長預測',
    content: '在「生長預測」頁面，您可以選擇一隻羊，系統將使用 AI 模型預測其未來的生長曲線。'
  },
  {
    title: '教學結束',
    content: '您已完成基本功能導覽。現在就開始使用領頭羊博士，體驗智慧化的羊隻管理吧！'
  }
];

const currentStep = computed(() => steps[currentStepIndex.value]);
const isLastStep = computed(() => currentStepIndex.value === steps.length - 1);

watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal;
  if (newVal) {
    currentStepIndex.value = 0; // Reset to first step when opened
  }
});

const handleClose = () => {
  emit('update:visible', false);
};

const prevStep = () => {
  if (currentStepIndex.value > 0) {
    currentStepIndex.value--;
  }
};

const nextStep = () => {
  if (isLastStep.value) {
    handleClose();
  } else {
    currentStepIndex.value++;
  }
};
</script>

<style scoped>
.guide-content {
  line-height: 1.6;
}
.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
</style>
