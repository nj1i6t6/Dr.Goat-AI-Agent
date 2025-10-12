<template>
  <div class="app-shell" :class="{ 'is-collapsed': isSidebarCollapsed && !isMobile }">
    <header class="app-header">
      <button
        v-if="isMobile"
        class="app-header__hamburger"
        type="button"
        aria-label="開啟導覽"
        @click="mobileSidebarOpen = true"
      >
        <el-icon><Menu /></el-icon>
      </button>
      <div class="app-header__brand" @click="$router.push('/dashboard')">
        <img :src="logoUrl" alt="Dr.Goat" class="app-header__logo" />
        <div class="app-header__brand-text">
          <span class="app-header__title">領頭羊博士</span>
          <span class="app-header__subtitle">Aurora Biophilic Tech Console</span>
        </div>
      </div>
      <div class="app-header__actions">
        <el-tooltip content="檢視任務提醒">
          <el-button
            circle
            size="small"
            class="app-header__action"
            @click="$router.push('/task-reminders')"
          >
            <el-icon><AlarmClock /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip content="重新整理內容">
          <el-button circle size="small" class="app-header__action" @click="reloadPage">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </el-tooltip>
        <div class="app-header__divider" />
        <div class="app-header__user">
          <span class="app-header__username">{{ authStore.username }}</span>
          <el-button size="small" plain type="danger" class="app-header__logout" @click="handleLogout">
            登出
          </el-button>
        </div>
      </div>
    </header>

    <div class="app-body">
      <transition name="sidebar-slide">
        <SidebarNav
          v-if="!isMobile || mobileSidebarOpen"
          :collapsed="isSidebarCollapsed && !isMobile"
          :is-mobile="isMobile"
          :mobile-open="mobileSidebarOpen"
          :username="authStore.username"
          :is-dark="isDark"
          :motion-enabled="motionEnabled"
          @toggle-collapse="toggleSidebar"
          @close-mobile="mobileSidebarOpen = false"
          @logout="handleLogout"
          @toggle-color-scheme="toggleColorScheme"
          @toggle-motion="toggleMotion"
        />
      </transition>

      <main class="app-main">
        <div class="app-main__surface aurora-scrollbar">
          <router-view />
        </div>
      </main>
    </div>

    <transition name="overlay-fade">
      <div
        v-if="isMobile && mobileSidebarOpen"
        class="app-overlay"
        @click="mobileSidebarOpen = false"
      ></div>
    </transition>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Menu, AlarmClock, Refresh } from '@element-plus/icons-vue';
import SidebarNav from '@/components/layout/SidebarNav.vue';
import { useAuthStore } from '@/stores/auth';
import { useTheme } from '@/composables/useTheme';
import logoUrl from '@/assets/images/logo.svg';

const authStore = useAuthStore();
const { isDark, motionEnabled, toggleColorScheme, toggleMotion } = useTheme();

const isSidebarCollapsed = ref(false);
const isMobile = ref(false);
const mobileSidebarOpen = ref(false);

const handleLogout = () => {
  ElMessageBox.confirm('您確定要登出嗎？', '提示', {
    confirmButtonText: '確定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      await authStore.logout();
      ElMessage({ type: 'success', message: '您已成功登出' });
    })
    .catch(() => {});
};

const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value;
};

const reloadPage = () => {
  window.dispatchEvent(new CustomEvent('aurora:refresh-requested'));
};

const evaluateViewport = () => {
  const mobile = window.innerWidth <= 768;
  isMobile.value = mobile;
  if (!mobile) {
    mobileSidebarOpen.value = false;
  }
};

onMounted(() => {
  evaluateViewport();
  window.addEventListener('resize', evaluateViewport);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', evaluateViewport);
});
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: radial-gradient(circle at top left, rgba(59, 130, 246, 0.12), transparent 45%),
    radial-gradient(circle at bottom right, rgba(45, 212, 191, 0.12), transparent 40%),
    #0f172a;
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 1100;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 28px;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(18px);
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.28);
}

.app-header__hamburger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: rgba(30, 64, 175, 0.35);
  color: #e2e8f0;
  cursor: pointer;
}

.app-header__brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  color: inherit;
  text-decoration: none;
}

.app-header__logo {
  width: 44px;
  height: 44px;
}

.app-header__brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.app-header__title {
  font-size: 1.3rem;
  font-weight: 700;
  color: #f8fafc;
}

.app-header__subtitle {
  font-size: 0.75rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(226, 232, 240, 0.7);
}

.app-header__actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-header__action {
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #0f172a;
}

.app-header__divider {
  width: 1px;
  height: 28px;
  background: linear-gradient(180deg, transparent, rgba(148, 163, 184, 0.5), transparent);
}

.app-header__user {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #f8fafc;
}

.app-header__username {
  font-weight: 600;
}

.app-header__logout {
  border-radius: 999px;
}

.app-body {
  display: flex;
  flex: 1;
  min-height: 0;
}

.app-main {
  flex: 1;
  padding: 32px 36px 48px;
  box-sizing: border-box;
  display: flex;
  justify-content: center;
}

.app-main__surface {
  width: 100%;
  max-width: 1360px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.32);
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.18);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.45);
  padding: 32px;
  box-sizing: border-box;
}

.app-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.58);
  z-index: 1000;
}

.sidebar-slide-enter-active,
.sidebar-slide-leave-active {
  transition: transform 0.28s ease;
}

.sidebar-slide-enter-from,
.sidebar-slide-leave-to {
  transform: translateX(-100%);
}

.overlay-fade-enter-active,
.overlay-fade-leave-active {
  transition: opacity 0.2s ease;
}

.overlay-fade-enter-from,
.overlay-fade-leave-to {
  opacity: 0;
}

@media (max-width: 1024px) {
  .app-main {
    padding: 24px;
  }

  .app-main__surface {
    padding: 24px;
    border-radius: 20px;
  }
}

@media (max-width: 768px) {
  .app-header {
    padding: 12px 18px;
  }

  .app-header__brand-text {
    display: none;
  }

  .app-main {
    padding: 18px;
  }

  .app-main__surface {
    padding: 18px;
    border-radius: 18px;
  }
}
</style>
