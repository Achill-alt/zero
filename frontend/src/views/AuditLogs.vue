<template>
  <div class="audit-logs">
    <div class="page-header">
      <h2>审计日志</h2>
      <p class="page-desc">系统操作审计追踪记录</p>
    </div>

    <!-- 统计概览 -->
    <div class="stat-row">
      <div class="stat-item">
        <span class="stat-num">{{ total }}</span>
        <span class="stat-label">总记录</span>
      </div>
      <div class="stat-item">
        <span class="stat-num">{{ logs.length }}</span>
        <span class="stat-label">当前页</span>
      </div>
    </div>

    <!-- 时间线 -->
    <el-card class="timeline-card" v-loading="loading">
      <el-timeline v-if="logs.length > 0">
        <el-timeline-item
          v-for="log in logs"
          :key="log.id"
          :timestamp="log.created_at"
          :color="log.action_color"
          placement="top"
          :icon="actionIcon(log.action)"
          size="large"
        >
          <div class="tl-item">
            <div class="tl-header">
              <span class="tl-user">{{ log.username }}</span>
              <el-tag
                :color="log.action_color"
                effect="dark"
                size="small"
                class="tl-action-tag"
              >
                {{ log.action_text }}
              </el-tag>
              <span class="tl-target">{{ log.target_text }}</span>
            </div>
            <p class="tl-desc">{{ log.description }}</p>
          </div>
        </el-timeline-item>
      </el-timeline>
      <div v-else class="empty-hint">
        <el-icon :size="32" color="#c0c4cc"><Document /></el-icon>
        <span>暂无审计日志</span>
      </div>
    </el-card>

    <!-- 分页 -->
    <el-pagination
      v-if="total > pageSize"
      v-model:current-page="page"
      :page-size="pageSize"
      :total="total"
      layout="total, prev, pager, next"
      @current-change="fetchLogs"
      style="margin-top: 16px; justify-content: flex-end"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, shallowRef } from 'vue'
import { adminApi } from '../api/admin'
import {
  User, Edit, Check, Close, Setting, Upload, Document,
  CircleCheck, CircleClose, RefreshRight, Delete, Plus, ArrowDown,
} from '@element-plus/icons-vue'

interface AuditLog {
  id: number
  user_id: number
  username: string
  action: string
  action_text: string
  action_color: string
  target_type: string
  target_text: string
  target_id: number
  detail: string | null
  description: string
  created_at: string
}

const logs = ref<AuditLog[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

onMounted(() => fetchLogs())

async function fetchLogs() {
  loading.value = true
  try {
    const res = await adminApi.auditLogs({ page: page.value, page_size: pageSize.value })
    logs.value = res.data.items as AuditLog[]
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

const iconMap: Record<string, any> = {
  contract_create:       Plus,
  contract_update:       Edit,
  contract_submit:       Upload,
  contract_approve:      CircleCheck,
  contract_reject:       CircleClose,
  contract_withdraw:     RefreshRight,
  contract_archive:      Check,
  contract_void:         Close,
  template_create:       Plus,
  template_update:       Edit,
  template_delete:       Delete,
  user_update:           Edit,
  approval_chain_create: Setting,
  approval_chain_update: Setting,
  LOGIN:                 User,
  LOGOUT:                ArrowDown,
  CREATE:                Plus,
  SUBMIT:                Upload,
  APPROVE:               CircleCheck,
  REJECT:                CircleClose,
  CONFIGURE:             Setting,
}
const defaultIcon = Document

function actionIcon(action: string) {
  // Use shallowRef-compatible return
  return iconMap[action] || defaultIcon
}
</script>

<style scoped>
/* ── Page header ──────────────────────────────────────── */
.page-header {
  margin-bottom: var(--space-5);
}
.page-header h2 {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
}
.page-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-top: var(--space-1);
}

/* ── Stat row ─────────────────────────────────────────── */
.stat-row {
  display: flex;
  gap: var(--space-6);
  margin-bottom: var(--space-5);
}
.stat-item {
  display: flex;
  flex-direction: column;
}
.stat-num {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-primary);
}
.stat-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-top: 2px;
}

/* ── Timeline card ────────────────────────────────────── */
.timeline-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

/* ── Timeline item ────────────────────────────────────── */
.tl-item {
  padding: var(--space-1) 0;
}
.tl-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-1);
}
.tl-user {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  font-size: var(--font-size-base);
}
.tl-action-tag {
  border-radius: var(--radius-full) !important;
  border: none !important;
  font-size: var(--font-size-xs);
}
.tl-target {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  background: var(--color-bg-secondary);
  padding: 1px 8px;
  border-radius: var(--radius-sm);
}
.tl-desc {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
}

/* ── Empty state ──────────────────────────────────────── */
.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-10) 0;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
}
</style>
