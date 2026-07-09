<template>
  <div class="app-shell">
    <template v-if="authStore.isLoggedIn">
      <AppNavbar />
      <div class="main-wrapper">
        <AppSidebar />
        <main class="main-content">
          <router-view v-slot="{ Component }">
            <transition name="page-fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </main>
      </div>
    </template>
    <template v-else>
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </template>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '../stores/auth'
import AppNavbar from './AppNavbar.vue'
import AppSidebar from './AppSidebar.vue'

const authStore = useAuthStore()
</script>

<style>
/* ── Reset & Base ────────────────────────────────────────────────── */
*,
*::before,
*::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  color: var(--color-text);
  background: var(--color-bg);
}

/* ── Scrollbar ──────────────────────────────────────────────────── */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: var(--radius-full);
}
::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-tertiary);
}

/* ── Layout ─────────────────────────────────────────────────────── */
.app-shell {
  min-height: 100vh;
  background: var(--color-bg);
}
.main-wrapper {
  display: flex;
  min-height: calc(100vh - var(--navbar-height));
}
.main-content {
  flex: 1;
  padding: var(--space-6);
  overflow-y: auto;
  max-width: var(--content-max-width);
}

/* ── Page transition ────────────────────────────────────────────── */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity var(--transition-fast), transform var(--transition-fast);
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* ── Shared page header utility ─────────────────────────────────── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-5);
}
.page-header h2 {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
  margin: 0;
}
.page-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-top: var(--space-1);
}

/* ── Element Plus overrides ─────────────────────────────────────── */
/* Refine el-button */
.el-button--primary {
  --el-button-bg-color: var(--color-primary);
  --el-button-border-color: var(--color-primary);
  --el-button-hover-bg-color: var(--color-primary-hover);
  --el-button-hover-border-color: var(--color-primary-hover);
  --el-button-active-bg-color: var(--color-primary-active);
  --el-button-active-border-color: var(--color-primary-active);
}

/* Refine el-card */
.el-card {
  border-radius: var(--radius-lg) !important;
  border: 1px solid var(--color-border) !important;
  box-shadow: var(--shadow-xs) !important;
  transition: box-shadow var(--transition-fast);
}
.el-card:hover {
  box-shadow: var(--shadow-sm) !important;
}
.el-card__header {
  border-bottom: 1px solid var(--color-border-light) !important;
  padding: var(--space-4) var(--space-5) !important;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-md);
  color: var(--color-text);
}

/* Refine el-table */
.el-table {
  border-radius: var(--radius-md);
  --el-table-border-color: var(--color-border-light);
}
.el-table th.el-table__cell {
  background: var(--color-bg);
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-sm);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Refine el-tag */
.el-tag {
  border-radius: var(--radius-sm);
  font-weight: var(--font-weight-medium);
}

/* Refine el-menu */
.el-menu {
  border-right: none !important;
}

/* Refine el-pagination */
.el-pagination {
  justify-content: flex-end;
  margin-top: var(--space-4);
}

/* Refine el-input / el-select */
.el-input__wrapper,
.el-select .el-input__wrapper {
  border-radius: var(--radius-md) !important;
  box-shadow: 0 0 0 1px var(--color-border) !important;
  transition: box-shadow var(--transition-fast);
}
.el-input__wrapper:hover,
.el-select:hover .el-input__wrapper {
  box-shadow: 0 0 0 1px var(--color-text-tertiary) !important;
}
.el-input.is-focus .el-input__wrapper,
.el-select.is-focus .el-input__wrapper {
  box-shadow: 0 0 0 1px var(--color-primary) !important;
}

/* Refine el-descriptions */
.el-descriptions {
  --el-descriptions-border-color: var(--color-border-light);
}
.el-descriptions__label {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
}

/* Refine el-timeline */
.el-timeline-item__node {
  border-color: var(--color-border);
}

/* Refine dialog */
.el-dialog {
  border-radius: var(--radius-xl);
}

/* Refine message box */
.el-message-box {
  border-radius: var(--radius-xl);
}
</style>
