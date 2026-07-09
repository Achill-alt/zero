<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <div class="progress-bar" :class="{ active: visible, finish: progress === 100 }" :style="{ width: progress + '%' }" />
      <AppLayout />
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { onErrorCaptured } from 'vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import AppLayout from './components/AppLayout.vue'
import { useProgressBar } from './composables/useProgressBar'

const { progress, visible } = useProgressBar()

onErrorCaptured((err: unknown, _instance, info: string) => {
  console.error('[App Error]', err, info)
  return false
})
</script>

<style>
.progress-bar {
  position: fixed;
  top: 0;
  left: 0;
  height: 3px;
  background: var(--color-primary);
  z-index: var(--z-progress);
  width: 0;
  opacity: 0;
  transition: width 0.3s ease, opacity 0.3s ease;
  pointer-events: none;
  border-radius: 0 2px 2px 0;
  box-shadow: 0 0 8px rgba(59, 109, 240, 0.4);
}
.progress-bar.active {
  opacity: 1;
}
.progress-bar.finish {
  width: 100% !important;
  opacity: 0;
  transition: width 0.2s ease, opacity 0.4s ease 0.2s;
}
</style>
