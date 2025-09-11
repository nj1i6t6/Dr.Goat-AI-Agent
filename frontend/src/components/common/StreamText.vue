<template>
  <div class="stream-text">
    <div v-html="renderedHtml"></div>
    <div v-if="loading" class="loading-line">
      <span class="cursor">▋</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue';
import MarkdownIt from 'markdown-it';

const props = defineProps({
  source: { type: String, default: '' },
  loading: { type: Boolean, default: false },
});

const renderedHtml = ref('');
const md = new MarkdownIt({ breaks: true, linkify: true, html: true });

function isProbablyHtml(str) {
  return /<\w+[^>]*>/.test(str || '');
}

watch(() => props.source, (val) => {
  if (isProbablyHtml(val)) {
    renderedHtml.value = val || '';
  } else {
    renderedHtml.value = md.render(val || '');
  }
}, { immediate: true });

onMounted(() => {
  const val = props.source || '';
  renderedHtml.value = isProbablyHtml(val) ? val : md.render(val);
});
onBeforeUnmount(() => {});
</script>

<style scoped>
.loading-line { opacity: 0.7; }
.cursor { animation: blink 1s step-end infinite; color: #6b7280; }
@keyframes blink { 50% { opacity: 0; } }
</style>
