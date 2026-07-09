<template>
  <div class="expiring-panel">
    <div class="page-header">
      <h2>预警面板</h2>
      <p class="page-desc">监控即将到期和已过期的合同</p>
    </div>

    <div class="stat-grid">
      <div class="stat-card" v-for="s in statCards" :key="s.label">
        <div class="stat-value" :style="{ color: s.color }">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>

    <el-card header="到期/已过期合同列表" style="margin-top:var(--space-5)">
      <el-table :data="items" stripe v-loading="loading" empty-text="暂无到期或过期合同">
        <el-table-column prop="title" label="合同标题" show-overflow-tooltip />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.expired ? 'danger' : 'warning'" effect="plain">
              {{ row.expired ? '已过期' : row.days_left + '天后到期' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="end_date" label="截止日期" width="120" />
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="$router.push(`/contracts/${row.id}`)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { contractApi } from '../api/contracts'

interface ExpiringItem {
  id: number
  title: string
  end_date: string
  expired: boolean
  days_left: number
}

interface StatCard {
  label: string
  value: number
  color: string
}

const items = ref<ExpiringItem[]>([])
const loading = ref(false)

const statCards = computed<StatCard[]>(() => [
  { label: '已过期', value: items.value.filter(i => i.expired).length, color: 'var(--color-danger)' },
  { label: '7天内到期', value: items.value.filter(i => !i.expired && i.days_left <= 7).length, color: 'var(--color-warning)' },
  { label: '30天内到期', value: items.value.filter(i => !i.expired && i.days_left > 7).length, color: 'var(--color-primary)' },
])

onMounted(async () => {
  loading.value = true
  try {
    const res = await contractApi.expiring({ days: 30, page: 1, page_size: 100 })
    items.value = res.data.items as ExpiringItem[]
  } finally { loading.value = false }
})
</script>

<style scoped>
.page-header { margin-bottom: var(--space-6); }
.page-header h2 { font-size: var(--font-size-2xl); font-weight: var(--font-weight-bold); color: var(--color-text); }
.page-desc { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-top: var(--space-1); }

.stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-4); }
.stat-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  text-align: center;
  transition: all var(--transition-fast);
}
.stat-card:hover { box-shadow: var(--shadow-md); transform: translateY(-1px); }
.stat-value { font-size: var(--font-size-3xl); font-weight: var(--font-weight-bold); line-height: var(--line-height-tight); }
.stat-label { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-top: var(--space-2); }

@media (max-width: 768px) {
  .stat-grid { grid-template-columns: 1fr; }
}
</style>
