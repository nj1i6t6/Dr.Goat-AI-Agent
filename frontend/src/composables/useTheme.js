import { storeToRefs } from 'pinia';
import { computed, watch } from 'vue';
import { useThemeStore } from '@/stores/theme';

const THEME_COLOR_META = 'theme-color';

function updateThemeColorMeta(isDark) {
  if (typeof document === 'undefined') return;
  let meta = document.querySelector(`meta[name="${THEME_COLOR_META}"]`);
  if (!meta) {
    meta = document.createElement('meta');
    meta.setAttribute('name', THEME_COLOR_META);
    document.head.appendChild(meta);
  }
  meta.setAttribute('content', isDark ? '#0f172a' : '#eef2ff');
}

export function useTheme() {
  const themeStore = useThemeStore();
  const { colorScheme, motionEnabled, isDark, motionPreference } = storeToRefs(themeStore);

  watch(
    isDark,
    (value) => {
      updateThemeColorMeta(value);
    },
    { immediate: true }
  );

  const auroraAccentClass = computed(() => (isDark.value ? 'aurora-dark' : 'aurora-light'));

  return {
    colorScheme,
    motionEnabled,
    isDark,
    motionPreference,
    auroraAccentClass,
    setColorScheme: themeStore.setColorScheme,
    toggleColorScheme: themeStore.toggleColorScheme,
    setMotionEnabled: themeStore.setMotionEnabled,
    toggleMotion: themeStore.toggleMotion,
  };
}
