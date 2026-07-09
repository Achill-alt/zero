<template>
  <div class="audit-logs">
    <div class="page-header">
      <h2>审计日志</h2>
      <p class="page-desc">系统操作审计追踪记录</p>
    </div>
    <el-table :data="logs" stripe style="margin-top:var(--space-4)" v-loading="loading">
      <el-table-column prop="created_at" label="时间" width="170" />
      <el-table-column prop="user_id" label="用户ID" width="80" />
      <el-table-column label="操作" width="140">
        <template #default="{row}"><el-tag>{{ actionText(row.action) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="target_type" label="目标类型" width="120" />
      <el-table-column prop="target_id" label="目标ID" width="80" />
      <el-table-column prop="detail" label="详情" min-width="200" />
    </el-table>
    <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="fetchLogs" style="margin-top:16px;justify-content:flex-end" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi } from '../api/admin'

interface AuditLog {
  created_at: string
  user_id: number
  action: string
  target_type: string
  target_id: number
  detail: string
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
    logs.value = res.data.items
    total.value = res.data.total
  } finally { loading.value = false }
}

function actionText(a: string): string {
  const map: Record<string, string> = {
    login: '登录', logout: '退出', contract_create: '创建合同', contract_update: '编辑合同',
    contract_submit: '提交审批', contract_approve: '审批通过', contract_reject: '审批驳回',
    contract_withdraw: '撤回审批', contract_archive: '归档', contract_void: '作废',
    template_create: '创建模板', user_create: '创建用户', user_update: '编辑用户',
    approval_chain_create: '创建审批链', approval_chain_update: '编辑审批链',
  }
  return map[a] || a
}
</script>
