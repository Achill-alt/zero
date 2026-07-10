<template>
  <div class="dashboard">
    <div class="page-header">
      <h2>工作台</h2>
      <p class="page-desc">合同管理概览与快捷操作</p>
    </div>

    <!-- Stat cards -->
    <div class="stat-grid">
      <div class="stat-card" v-for="stat in stats" :key="stat.label">
        <div class="stat-icon" :style="{ background: stat.bg, color: stat.color }">
          <el-icon :size="24"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </div>

    <!-- Recent contracts + Expiry warnings -->
    <div class="dashboard-grid">
      <div class="dash-main">
        <el-card header="最近合同">
          <el-table :data="recentContracts" stripe v-loading="loading" empty-text="暂无合同数据">
            <el-table-column prop="title" label="合同标题" show-overflow-tooltip />
            <el-table-column prop="contract_type" label="类型" width="90">
              <template #default="{ row }">
                <el-tag size="small" type="info">{{ typeText(row.contract_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="statusTag(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="170" />
            <el-table-column label="操作" width="80" fixed="right">
              <template #default="{ row }">
                <el-button size="small" text type="primary" @click="$router.push(`/contracts/${row.id}`)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>

      <div class="dash-side">
        <el-card header="到期预警">
          <div v-if="loading" style="text-align:center;padding:20px">
            <el-icon class="is-loading" :size="20"><Loading /></el-icon>
          </div>
          <div v-else-if="expiring.length === 0" class="empty-hint">
            <el-icon :size="28" color="#c0c4cc"><CircleCheck /></el-icon>
            <span>暂无即将到期合同</span>
          </div>
          <div v-for="item in expiring" :key="item.id" class="expiring-item" @click="$router.push(`/contracts/${item.id}`)">
            <div class="expiring-info">
              <span class="expiring-title">{{ item.title }}</span>
              <span class="expiring-date">{{ item.end_date }}</span>
            </div>
            <el-tag :type="item.expired ? 'danger' : 'warning'" size="small" effect="plain">
              {{ item.expired ? '已过期' : item.days_left + '天后到期' }}
            </el-tag>
          </div>
        </el-card>
      </div>
    </div>

    <!-- Quick actions -->
    <div class="quick-actions">
      <el-button type="primary" size="large" @click="$router.push('/contracts/create')">
        <el-icon><Edit /></el-icon> 拟制合同
      </el-button>
      <el-button v-if="authStore.isApprover || authStore.isAdmin" size="large" @click="$router.push('/approvals')">
        <el-icon><Checked /></el-icon> 审批中心
      </el-button>
      <el-button size="large" @click="$router.push('/expiring')">
        <el-icon><Clock /></el-icon> 预警面板
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { contractApi } from '../api/contracts'
import { statusTag, statusText, typeText } from '../composables/useStatus'

interface StatItem {
  label: string
  value: number
  icon: string
  color: string
  bg: string
}

interface ExpiringItem {
  id: number
  title: string
  end_date: string
  expired: boolean
  days_left: number
}

const authStore = useAuthStore()
const loading = ref(false)

const stats = ref<StatItem[]>([
  { label: '合同总数', value: 0, icon: 'Document', color: '#3b6df0', bg: '#ebf0fe' },
  { label: '审批中', value: 0, icon: 'Clock', color: '#f59e0b', bg: '#fff8e6' },
  { label: '已归档', value: 0, icon: 'CircleCheck', color: '#1aae6b', bg: '#e6f7ee' },
  { label: '即将到期', value: 0, icon: 'Warning', color: '#ef4444', bg: '#fef2f2' },
])
const recentContracts = ref<any[]>([])
const expiring = ref<ExpiringItem[]>([])

onMounted(async () => {
  loading.value = true
  try {
    const [listRes, pendingRes, archivedRes, expRes] = await Promise.all([
      contractApi.list({ page: 1, page_size: 5 }),
      contractApi.list({ page: 1, page_size: 1, status: 'pending_approval' }),
      contractApi.list({ page: 1, page_size: 1, status: 'archived' }),
      contractApi.expiring({ days: 30, page: 1, page_size: 5 }),
    ])
    recentContracts.value = listRes.data.items
    stats.value[0].value = listRes.data.total
    stats.value[1].value = pendingRes.data.total
    stats.value[2].value = archivedRes.data.total
    expiring.value = expRes.data.items
    stats.value[3].value = expRes.data.total_upcoming
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
/* ── Page header ───────────────────────────────────────────────── */
.page-header {
  margin-bottom: var(--space-6);
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

/* ── Stat grid ─────────────────────────────────────────────────── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}
.stat-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  transition: all var(--transition-fast);
  cursor: default;
}
.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}
.stat-icon {
  width: 48px; height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-value {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
  line-height: var(--line-height-tight);
}
.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-top: var(--space-1);
}

/* ── Dashboard grid ────────────────────────────────────────────── */
.dashboard-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--space-5);
  margin-bottom: var(--space-5);
}

/* ── Expiring items ────────────────────────────────────────────── */
.expiring-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--color-border-light);
  cursor: pointer;
  transition: color var(--transition-fast);
}
.expiring-item:last-child { border-bottom: none; }
.expiring-item:hover { color: var(--color-primary); }
.expiring-info { flex: 1; min-width: 0; }
.expiring-title {
  font-size: var(--font-size-base);
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.expiring-date {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}
.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-6) 0;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
}

/* ── Quick actions ─────────────────────────────────────────────── */
.quick-actions {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}

/* ── Responsive ────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .dashboard-grid { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .stat-grid { grid-template-columns: 1fr; }
}
</style>
