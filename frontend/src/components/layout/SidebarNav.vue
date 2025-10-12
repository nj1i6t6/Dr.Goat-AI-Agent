<template>
  <aside
    class="sidebar"
    :class="{
      'is-collapsed': collapsed && !isMobile,
      'is-mobile': isMobile,
      'is-mobile-open': isMobile && mobileOpen,
    }"
  >
    <div class="sidebar__top">
      <button
        v-if="isMobile"
        class="sidebar__close"
        type="button"
        @click="$emit('close-mobile')"
        aria-label="關閉導覽"
      >
        <el-icon><Close /></el-icon>
      </button>

      <div class="sidebar__brand" @click="navigateTo('/dashboard')">
        <img :src="logoUrl" alt="Dr.Goat" class="sidebar__logo" />
        <div v-if="!collapsed || isMobile" class="sidebar__brand-meta">
          <p class="sidebar__brand-title">領頭羊博士</p>
          <p class="sidebar__brand-subtitle">Dr.Goat AI Agent</p>
        </div>
      </div>

      <div v-if="!collapsed || isMobile" class="sidebar__user">
        <div class="sidebar__user-info">
          <span class="sidebar__user-name">{{ username }}</span>
          <span class="sidebar__user-role">用戶名稱/登出</span>
        </div>
        <el-button class="sidebar__logout" size="small" type="danger" plain @click="emitLogout">
          登出
        </el-button>
      </div>
    </div>

    <nav class="sidebar__nav">
      <ul class="nav-list">
        <li v-for="item in navItems" :key="item.id" class="nav-item">
          <template v-if="item.type === 'section'">
            <button
            type="button"
            class="nav-button"
            :class="{
              'is-open': openSections.includes(item.id),
              'is-active': isSectionActive(item),
            }"
            @click="toggleSection(item.id)"
            >
              <el-icon class="nav-button__icon"><component :is="item.icon" /></el-icon>
              <span v-if="!collapsed || isMobile" class="nav-button__label">{{ item.label }}</span>
              <el-icon v-if="!collapsed || isMobile" class="nav-button__chevron">
                <ArrowRight :class="{ 'is-rotated': openSections.includes(item.id) }" />
              </el-icon>
            </button>
            <transition name="accordion">
              <ul
                v-if="openSections.includes(item.id) && (!collapsed || isMobile)"
                class="nav-sub-list"
              >
                <li
                  v-for="child in item.children"
                  :key="child.id"
                  class="nav-sub-item"
                >
                  <RouterLink
                    :to="child.route"
                    class="nav-sub-link"
                    :class="{ 'is-active': isActive(child.route) }"
                    @click="handleNavigate"
                  >
                    <el-icon class="nav-sub-icon"><component :is="child.icon" /></el-icon>
                    <span class="nav-sub-label">{{ child.label }}</span>
                  </RouterLink>
                </li>
              </ul>
            </transition>
          </template>

          <RouterLink
            v-else
            :to="item.route"
            class="nav-button nav-link"
            :class="{ 'is-active': isActive(item.route) }"
            @click="handleNavigate"
          >
            <el-icon class="nav-button__icon"><component :is="item.icon" /></el-icon>
            <span v-if="!collapsed || isMobile" class="nav-button__label">{{ item.label }}</span>
          </RouterLink>
        </li>
      </ul>
    </nav>

    <div class="sidebar__footer">
      <div class="sidebar__divider" />
      <div class="sidebar__controls">
        <div class="sidebar__toggle" :class="{ 'is-collapsed': collapsed && !isMobile }">
          <el-icon class="sidebar__toggle-icon"><Sunny /></el-icon>
          <span v-if="!collapsed || isMobile" class="sidebar__toggle-label">深/淺色模式</span>
          <el-switch
            :model-value="isDark"
            size="small"
            @change="$emit('toggle-color-scheme')"
          />
        </div>
        <div
          v-if="!collapsed || isMobile"
          class="sidebar__toggle"
        >
          <el-icon class="sidebar__toggle-icon"><MagicStick /></el-icon>
          <span class="sidebar__toggle-label">Aurora 動效</span>
          <el-switch
            :model-value="motionEnabled"
            size="small"
            @change="$emit('toggle-motion')"
          />
        </div>
      </div>
      <button class="sidebar__collapse" type="button" @click="$emit('toggle-collapse')">
        <el-icon>
          <DArrowRight v-if="collapsed && !isMobile" />
          <DArrowLeft v-else />
        </el-icon>
        <span v-if="!collapsed || isMobile">收合導覽列</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { useRouter, useRoute, RouterLink } from 'vue-router';
import {
  ArrowRight,
  Collection,
  Cpu,
  DataAnalysis,
  DocumentChecked,
  DArrowLeft,
  DArrowRight,
  Grid,
  Histogram,
  MagicStick,
  MenuBook,
  MessageBox,
  Monitor,
  Notebook,
  Opportunity,
  PieChart,
  Promotion,
  SetUp,
  Sunny,
  Timer,
  TrendCharts,
  Tickets,
  Close,
} from '@element-plus/icons-vue';
import logoUrl from '@/assets/images/logo.svg';

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false,
  },
  mobileOpen: {
    type: Boolean,
    default: false,
  },
  isMobile: {
    type: Boolean,
    default: false,
  },
  username: {
    type: String,
    default: '',
  },
  isDark: {
    type: Boolean,
    default: false,
  },
  motionEnabled: {
    type: Boolean,
    default: true,
  },
});

const emit = defineEmits(['toggle-collapse', 'close-mobile', 'logout', 'toggle-color-scheme', 'toggle-motion']);

const router = useRouter();
const route = useRoute();

const navItems = computed(() => [
  {
    id: 'dashboard',
    type: 'link',
    label: '代理人儀表板',
    icon: DataAnalysis,
    route: '/dashboard',
  },
  {
    id: 'daily-ops',
    type: 'section',
    label: '日常管理',
    icon: Notebook,
    children: [
      { id: 'flock', label: '羊群總覽', route: '/flock', icon: Tickets },
      { id: 'tasks', label: '任務提醒', route: '/task-reminders', icon: Timer },
    ],
  },
  {
    id: 'smart-goat',
    type: 'section',
    label: '智慧羊博士',
    icon: MessageBox,
    children: [
      { id: 'consultation', label: '營養代理人與 ESG 建議', route: '/consultation', icon: MenuBook },
      { id: 'chat', label: '羊博士問答', route: '/chat', icon: Promotion },
    ],
  },
  {
    id: 'data-intel',
    type: 'section',
    label: '數據與預測',
    icon: PieChart,
    children: [
      { id: 'prediction', label: '生長預測', route: '/prediction', icon: TrendCharts },
      { id: 'governance', label: '資料治理', route: '/analytics', icon: Histogram },
    ],
  },
  {
    id: 'sustainability',
    type: 'section',
    label: '永續與追溯',
    icon: Grid,
    children: [
      { id: 'traceability', label: '產銷履歷', route: '/traceability', icon: Collection },
      { id: 'esg-metrics', label: 'ESG 指標', route: '/data-management', icon: Opportunity },
    ],
  },
  {
    id: 'iot',
    type: 'section',
    label: '物聯網自動化',
    icon: Cpu,
    children: [
      { id: 'iot-dashboard', label: '物聯網儀表', route: '/iot-dashboard', icon: Monitor },
      { id: 'iot-management', label: 'IoT 裝置管理', route: '/iot', icon: DocumentChecked },
    ],
  },
  {
    id: 'settings',
    type: 'link',
    label: '系統設定',
    icon: SetUp,
    route: '/settings',
  },
]);

const openSections = ref([]);

const isActive = (targetRoute) => route.path.startsWith(targetRoute);

const ensureSectionVisibility = () => {
  const activePath = route.path;
  const matchingSection = navItems.value.find(
    (item) => item.type === 'section' && item.children.some((child) => activePath.startsWith(child.route))
  );
  if (matchingSection && !openSections.value.includes(matchingSection.id)) {
    openSections.value = [...openSections.value, matchingSection.id];
  }
};

watch(
  () => route.path,
  () => {
    ensureSectionVisibility();
    if (props.isMobile && props.mobileOpen) {
      emit('close-mobile');
    }
  },
  { immediate: true }
);

const toggleSection = (id) => {
  if (props.collapsed && !props.isMobile) {
    openSections.value = openSections.value.includes(id) ? openSections.value : [id];
    return;
  }
  openSections.value = openSections.value.includes(id)
    ? openSections.value.filter((sectionId) => sectionId !== id)
    : [...openSections.value, id];
};

const isSectionActive = (section) => section.children.some((child) => isActive(child.route));

const navigateTo = (path) => {
  router.push(path);
  handleNavigate();
};

const handleNavigate = () => {
  if (props.isMobile) {
    emit('close-mobile');
  }
};

const emitLogout = () => emit('logout');
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  width: 240px;
  min-height: 100vh;
  background: rgba(15, 23, 42, 0.92);
  color: #f8fafc;
  border-right: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 12px 0 40px rgba(15, 23, 42, 0.28);
  transition: width 0.28s ease, transform 0.3s ease;
  z-index: 1001;
}

.sidebar.is-collapsed {
  width: 72px;
}

.sidebar.is-mobile {
  position: fixed;
  left: 0;
  transform: translateX(-100%);
  width: 260px;
  min-height: 100dvh;
}

.sidebar.is-mobile.is-mobile-open {
  transform: translateX(0);
}

.sidebar__top {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px 20px;
}

.sidebar__close {
  align-self: flex-end;
  background: transparent;
  border: none;
  color: inherit;
  font-size: 20px;
  cursor: pointer;
}

.sidebar__brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.sidebar__logo {
  width: 42px;
  height: 42px;
}

.sidebar__brand-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
}

.sidebar__brand-subtitle {
  margin: 0;
  font-size: 0.7rem;
  letter-spacing: 0.08em;
  opacity: 0.75;
}

.sidebar__user {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(30, 64, 175, 0.28);
  border: 1px solid rgba(148, 163, 184, 0.35);
}

.sidebar__user-info {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.sidebar__user-name {
  font-weight: 600;
}

.sidebar__user-role {
  font-size: 0.7rem;
  opacity: 0.8;
}

.sidebar__logout {
  border-radius: 999px;
}

.sidebar__nav {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px 16px;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.nav-item {
  display: flex;
  flex-direction: column;
}

.nav-button {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 14px;
  border-radius: 12px;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease;
  font-size: 0.95rem;
  text-align: left;
}

.nav-button:hover,
.nav-button.is-active {
  background: rgba(59, 130, 246, 0.24);
  color: #ffffff;
}

.nav-button__icon {
  font-size: 20px;
}

.nav-button__chevron {
  margin-left: auto;
  transition: transform 0.2s ease;
}

.nav-button__chevron .is-rotated {
  transform: rotate(90deg);
}

.nav-sub-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: 6px 0 10px;
  padding-left: 48px;
}

.nav-sub-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  color: rgba(226, 232, 240, 0.9);
  text-decoration: none;
  transition: background 0.2s ease, color 0.2s ease;
}

.nav-sub-link:hover,
.nav-sub-link.is-active {
  background: rgba(96, 165, 250, 0.24);
  color: #ffffff;
}

.nav-sub-icon {
  font-size: 18px;
}

.sidebar__footer {
  padding: 16px 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sidebar__divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.35), transparent);
}

.sidebar__controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sidebar__toggle {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(30, 58, 138, 0.35);
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.sidebar__toggle.is-collapsed {
  justify-content: center;
}

.sidebar__toggle-icon {
  font-size: 18px;
}

.sidebar__toggle-label {
  font-size: 0.85rem;
}

.sidebar__collapse {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: 0.9rem;
}

.sidebar__collapse:hover {
  background: rgba(59, 130, 246, 0.2);
}

.accordion-enter-active,
.accordion-leave-active {
  transition: all 0.2s ease;
}

.accordion-enter-from,
.accordion-leave-to {
  max-height: 0;
  opacity: 0;
}

.accordion-enter-to,
.accordion-leave-from {
  max-height: 400px;
  opacity: 1;
}

@media (max-width: 768px) {
  .sidebar {
    width: 260px;
  }

  .sidebar__nav {
    padding: 4px 12px 18px;
  }
}
</style>
