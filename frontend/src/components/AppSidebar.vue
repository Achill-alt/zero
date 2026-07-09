<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <span class="brand-icon">📋</span>
      <span class="brand-text">合同管理</span>
    </div>

    <el-menu
      :default-active="currentRoute"
      background-color="transparent"
      text-color="var(--color-text-secondary)"
      active-text-color="var(--color-primary)"
    >
      <el-menu-item index="/dashboard" @click="$router.push('/dashboard')">
        <el-icon><HomeFilled /></el-icon>
        <span>工作台</span>
      </el-menu-item>

      <el-menu-item index="/contracts" @click="$router.push('/contracts')">
        <el-icon><Document /></el-icon>
        <span>合同管理</span>
      </el-menu-item>

      <el-menu-item index="/contracts/create" @click="$router.push('/contracts/create')">
        <el-icon><Edit /></el-icon>
        <span>拟制合同</span>
      </el-menu-item>

      <el-menu-item index="/search" @click="$router.push('/search')">
        <el-icon><Search /></el-icon>
        <span>全文检索</span>
      </el-menu-item>

      <el-menu-item index="/notifications" @click="$router.push('/notifications')">
        <el-icon><Bell /></el-icon>
        <span>通知中心</span>
      </el-menu-item>

      <el-menu-item v-if="authStore.isApprover || authStore.isAdmin" index="/approvals" @click="$router.push('/approvals')">
        <el-icon><Checked /></el-icon>
        <span>审批中心</span>
      </el-menu-item>

      <el-menu-item index="/templates" @click="$router.push('/templates')">
        <el-icon><Files /></el-icon>
        <span>模板管理</span>
      </el-menu-item>

      <el-menu-item index="/expiring" @click="$router.push('/expiring')">
        <el-icon><Clock /></el-icon>
        <span>预警面板</span>
      </el-menu-item>

      <template v-if="authStore.isAdmin">
        <div class="sidebar-section-label">系统管理</div>
        <el-menu-item index="/admin/users" @click="$router.push('/admin/users')">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/approval-chains" @click="$router.push('/admin/approval-chains')">
          <el-icon><Setting /></el-icon>
          <span>审批链配置</span>
        </el-menu-item>
        <el-menu-item index="/admin/audit-logs" @click="$router.push('/admin/audit-logs')">
          <el-icon><List /></el-icon>
          <span>审计日志</span>
        </el-menu-item>
        <el-menu-item index="/admin/register" @click="$router.push('/admin/register')">
          <el-icon><Plus /></el-icon>
          <span>新增用户</span>
        </el-menu-item>
      </template>
    </el-menu>

    <div class="sidebar-footer">
      <span class="version">v1.2</span>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const authStore = useAuthStore()

const currentRoute = computed(() => {
  const path = route.path
  if (path.startsWith('/contracts')) {
    if (path === '/contracts/create') return '/contracts/create'
    return '/contracts'
  }
  if (path.startsWith('/admin')) return path
  return path
})
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  min-height: calc(100vh - var(--navbar-height));
  background: var(--color-bg-card);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

/* ── Brand ─────────────────────────────────────────────────────── */
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-5) var(--space-5) var(--space-4);
  border-bottom: 1px solid var(--color-border-light);
}
.brand-icon {
  font-size: var(--font-size-xl);
}
.brand-text {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  letter-spacing: 0.02em;
}

/* ── Menu ──────────────────────────────────────────────────────── */
.sidebar :deep(.el-menu) {
  flex: 1;
  padding: var(--space-2) 0;
  border-right: none !important;
}

.sidebar :deep(.el-menu-item) {
  margin: 2px var(--space-2);
  border-radius: var(--radius-md);
  height: 44px;
  line-height: 44px;
  font-size: var(--font-size-base);
  transition: all var(--transition-fast);
}

.sidebar :deep(.el-menu-item:hover) {
  background: var(--color-primary-light) !important;
  color: var(--color-primary) !important;
}

.sidebar :deep(.el-menu-item.is-active) {
  background: var(--color-primary-light) !important;
  color: var(--color-primary) !important;
  font-weight: var(--font-weight-semibold);
  position: relative;
}

.sidebar :deep(.el-menu-item.is-active)::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  background: var(--color-primary);
  border-radius: 0 2px 2px 0;
}

.sidebar :deep(.el-menu-item .el-icon) {
  font-size: var(--font-size-lg);
}

/* ── Section label ─────────────────────────────────────────────── */
.sidebar-section-label {
  padding: var(--space-4) var(--space-5) var(--space-2);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* ── Footer ────────────────────────────────────────────────────── */
.sidebar-footer {
  padding: var(--space-3) var(--space-5);
  border-top: 1px solid var(--color-border-light);
  text-align: center;
}
.version {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}
</style>
