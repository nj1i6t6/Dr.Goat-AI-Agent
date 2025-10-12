<template>
  <div class="empty-state">
    <div v-if="icon" class="empty-state__icon">
      <component v-if="isComponent" :is="icon" class="empty-state__icon-component" />
      <span v-else class="empty-state__icon-emoji">{{ icon }}</span>
    </div>
    <div class="empty-state__content">
      <h2 class="empty-state__title">{{ title }}</h2>
      <p class="empty-state__message">{{ message }}</p>
      <div v-if="$slots.default" class="empty-state__actions">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  icon: {
    type: [String, Object, Function],
    default: null,
  },
  title: {
    type: String,
    required: true,
  },
  message: {
    type: String,
    required: true,
  },
});

const isComponent = computed(
  () =>
    Boolean(props.icon) && (typeof props.icon === 'object' || typeof props.icon === 'function')
);
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 32px 24px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.38);
  border: 1px dashed rgba(148, 163, 184, 0.6);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
  gap: 18px;
}

.empty-state__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.18), rgba(45, 212, 191, 0.22));
  color: #0f172a;
  font-size: 36px;
}

.empty-state__icon-component {
  font-size: 42px;
}

.empty-state__icon-emoji {
  font-size: 40px;
  line-height: 1;
}

.empty-state__title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.empty-state__message {
  margin: 0;
  max-width: 480px;
  line-height: 1.6;
  color: #475569;
}

.empty-state__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

@media (max-width: 768px) {
  .empty-state {
    padding: 24px 18px;
  }

  .empty-state__title {
    font-size: 1.3rem;
  }
}
</style>
