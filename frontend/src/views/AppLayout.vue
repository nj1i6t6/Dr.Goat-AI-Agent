<template>
  <div class="app-layout-container">
    <el-header class="top-nav">
      <!-- Logo -->
      <div class="logo" @click="$router.push('/dashboard')">
        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0OCIgaGVpZ2h0PSI0OCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjEuNSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNOSAxNWMtMi41IDEuNS01LjI1IDIuNS04IDMiLz48cGF0aCBkPSJNMy41IDIxYzEuMjUtMS4xNyAyLTUuNSAzLTEwLjVjMC01LjM5IDEuNzctOC41IDIuNS05LjVjMS0xLjI1IDIuMjUtMS41IDQuNS0uNWMzLjM4IDEuNSAzLjUgMy41IDQuNSA5LjVjMCAuMzEgMCAxLjE5LS4wOCA1Ii8+PHBhdGggZD0iTTE4IDIxYzAgLTEuNDQtLjUtMy41LTEuNS01LjVjLTEtMi0yLjUtMy00LjUtMy41Ii8+PHBhdGggZD0iTTIyIDIwLjVjLTEuODEtMS4xNy0zLjc1LTEuNS01Ljg3LTEuNSIvPjxjaXJjbGUgY3g9IjEwIiBjeT0iMTAiIHI9IjEiLz48Y2lyY2xlIGN4PSIxNiIgY3k9IjEwIiByPSIxIi8+PC9zdmc+" alt="Logo" />
        <span>領頭羊博士</span>
      </div>

      <!-- 頂部導航菜單 (桌面版) -->
      <el-menu
        :default-active="$route.path"
        class="top-menu"
        mode="horizontal"
        :ellipsis="false"
        router
      >
        <el-menu-item index="/dashboard">代理人儀表板</el-menu-item>
        <el-menu-item index="/consultation">飼養建議諮詢</el-menu-item>
        <el-menu-item index="/chat">AI 問答助理</el-menu-item>
        <el-menu-item index="/flock">羊群總覽</el-menu-item>
        <el-menu-item index="/prediction">生長預測</el-menu-item>
        <el-menu-item index="/iot">智慧牧場 IoT</el-menu-item>
        <el-menu-item index="/traceability">產銷履歷管理</el-menu-item>
        <el-menu-item index="/data-management">數據管理</el-menu-item>
        <el-menu-item index="/settings">系統設定</el-menu-item>
      </el-menu>

      <!-- 用戶資訊與漢堡選單 -->
      <div class="right-panel">
        <div class="user-info">
          <span>{{ authStore.username }}</span>
          <el-button @click="handleLogout" type="danger" size="small" plain>登出</el-button>
        </div>
        <div class="hamburger-menu" @click="drawerVisible = true">
          <el-icon><Menu /></el-icon>
        </div>
      </div>
    </el-header>

    <!-- 抽屜菜單 (移動版) -->
    <el-drawer
      v-model="drawerVisible"
      title="導航選單"
      direction="rtl"
      :with-header="true"
      size="260px"
    >
      <el-menu
        :default-active="$route.path"
        class="drawer-menu"
        router
        @select="drawerVisible = false"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>代理人儀表板</span>
        </el-menu-item>
        <el-menu-item index="/consultation">
          <el-icon><HelpFilled /></el-icon>
          <span>飼養建議諮詢</span>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><Service /></el-icon>
          <span>AI 問答助理</span>
        </el-menu-item>
        <el-menu-item index="/flock">
          <el-icon><Tickets /></el-icon>
          <span>羊群總覽</span>
        </el-menu-item>
        <el-menu-item index="/prediction">
          <el-icon><TrendCharts /></el-icon>
          <span>生長預測</span>
        </el-menu-item>
        <el-menu-item index="/iot">
          <el-icon><Cpu /></el-icon>
          <span>智慧牧場 IoT</span>
        </el-menu-item>
        <el-menu-item index="/traceability">
          <el-icon><Collection /></el-icon>
          <span>產銷履歷管理</span>
        </el-menu-item>
        <el-menu-item index="/data-management">
          <el-icon><Upload /></el-icon>
          <span>數據管理</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系統設定</span>
        </el-menu-item>
      </el-menu>
    </el-drawer>

    <!-- 主內容區域 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from '../stores/auth';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  Menu,
  DataAnalysis,
  HelpFilled,
  Service,
  Tickets,
  Upload,
  Setting,
  TrendCharts,
  Collection,
  Cpu,
} from '@element-plus/icons-vue';

const authStore = useAuthStore();
const drawerVisible = ref(false);

const handleLogout = () => {
  ElMessageBox.confirm('您確定要登出嗎？', '提示', {
    confirmButtonText: '確定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    await authStore.logout();
    ElMessage({ type: 'success', message: '您已成功登出' });
  }).catch(() => {});
};
</script>

<style scoped>
.app-layout-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.top-nav {
  background-color: #3b82f6;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
  height: 60px;
  position: sticky;
  top: 0;
  z-index: 1000;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.logo {
  display: flex;
  align-items: center;
  cursor: pointer;
  margin-right: 20px;
}
.logo img {
  height: 32px;
  margin-right: 10px;
}
.logo span {
  font-size: 1.6em;
  font-weight: bold;
  color: white;
}

.top-menu {
  flex-grow: 1;
  background-color: transparent;
  border-bottom: none;
  height: 100%;
}

.top-menu .el-menu-item {
  color: #e2e8f0;
  font-size: 0.95em;
  font-weight: 500;
  background-color: transparent !important;
  border-bottom: 3px solid transparent !important;
}

.top-menu .el-menu-item:hover {
  background-color: rgba(255, 255, 255, 0.2) !important;
  color: white !important;
}

.top-menu .el-menu-item.is-active {
  color: white !important;
  border-bottom-color: #ffffff !important;
}

.right-panel {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.hamburger-menu {
  display: none;
  cursor: pointer;
  font-size: 24px;
}

.main-content {
  flex-grow: 1;
  padding: 25px;
  max-width: 1300px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.drawer-menu {
  border-right: none;
}

/* 響應式斷點 */
@media (max-width: 1024px) {
  .top-menu {
    display: none;
  }
  .hamburger-menu {
    display: block;
  }
  /* .user-info {
    在小螢幕也可以選擇隱藏部分用戶資訊
  } 
  */
}
</style>