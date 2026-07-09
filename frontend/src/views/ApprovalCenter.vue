<template>
  <div class="approval-center">
    <div class="page-header">
      <h2>审批中心</h2>
      <p class="page-desc">处理等待您审批的合同</p>
    </div>

    <el-table :data="items" stripe style="margin-top:var(--space-4)" v-loading="loading">
      <el-table-column prop="contract_title" label="合同标题" show-overflow-tooltip />
      <el-table-column label="类型" width="80">
        <template #default="{ row }">
          <el-tag size="small" type="info">{{ typeText(row.contract_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="金额" width="120">
        <template #default="{ row }">{{ row.amount ? '¥' + row.amount.toLocaleString() : '-' }}</template>
      </el-table-column>
      <el-table-column prop="template_name" label="审批链" width="140" show-overflow-tooltip />
      <el-table-column label="当前步骤" width="120">
        <template #default="{ row }">
          <el-tag size="small" type="warning" effect="plain">{{ row.current_step?.name }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="提交时间" width="170" />
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="success" @click="handleApprove(row)">通过</el-button>
          <el-button size="small" type="danger" @click="handleReject(row)">驳回</el-button>
          <el-button size="small" text type="primary" @click="$router.push(`/contracts/${row.contract_id}`)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && items.length === 0" description="暂无待审批合同">
      <el-button type="primary" @click="$router.push('/contracts')">浏览合同</el-button>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { approvalApi } from '../api/approvals'
import { typeText } from '../composables/useStatus'

interface PendingApproval {
  contract_id: number
  contract_title: string
  contract_type: string
  amount: number | null
  template_name: string
  current_step: { name: string }
  created_at: string
  instance_id: number
}

const items = ref<PendingApproval[]>([])
const loading = ref(false)

onMounted(() => fetchList())

async function fetchList(): Promise<void> {
  loading.value = true
  try {
    const res = await approvalApi.pending()
    items.value = (res.data?.items || []) as PendingApproval[]
  } finally { loading.value = false }
}

async function handleApprove(row: PendingApproval): Promise<void> {
  const { value: comment } = await ElMessageBox.prompt('请输入审批意见（可选）', '审批通过', {
    confirmButtonText: '通过', cancelButtonText: '取消',
  }).catch(() => ({ value: undefined }))
  if (comment === null || comment === undefined) return
  await approvalApi.approve(row.instance_id, comment || '')
  ElMessage.success('审批通过')
  fetchList()
}

async function handleReject(row: PendingApproval): Promise<void> {
  const { value: comment } = await ElMessageBox.prompt('请输入驳回理由', '驳回审批', {
    confirmButtonText: '驳回', cancelButtonText: '取消',
  }).catch(() => ({ value: undefined }))
  if (!comment) { ElMessage.warning('请输入驳回理由'); return }
  await approvalApi.reject(row.instance_id, comment)
  ElMessage.success('已驳回')
  fetchList()
}
</script>

<style scoped>
.page-header { margin-bottom: var(--space-6); }
.page-header h2 { font-size: var(--font-size-2xl); font-weight: var(--font-weight-bold); color: var(--color-text); }
.page-desc { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-top: var(--space-1); }
</style>
