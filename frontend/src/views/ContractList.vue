<template>
  <div class="contract-list">
    <div class="page-header">
      <h2>合同管理</h2>
      <div style="display:flex;gap:8px">
        <el-dropdown @command="handleExport">
          <el-button>
            导出 <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="excel">导出 Excel (.xlsx)</el-dropdown-item>
              <el-dropdown-item command="pdf" :disabled="!pdfAvailable">
                导出 PDF (.pdf)<span v-if="!pdfAvailable" style="font-size:10px;color:#909399;margin-left:4px">（需 GTK3）</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button type="primary" @click="$router.push('/contracts/create')">
          <el-icon><Plus /></el-icon> 拟制合同
        </el-button>
      </div>
    </div>
    <div class="toolbar">
      <el-input v-model="search" placeholder="搜索合同标题..." style="width:250px" clearable />
      <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width:140px">
        <el-option label="草稿" value="draft" /><el-option label="审批中" value="pending_approval" />
        <el-option label="已通过" value="approved" /><el-option label="已归档" value="archived" /><el-option label="已作废" value="voided" />
      </el-select>
      <el-select v-model="filterType" placeholder="类型筛选" clearable style="width:140px">
        <el-option label="采购" value="purchase" /><el-option label="销售" value="sales" />
        <el-option label="服务" value="service" /><el-option label="租赁" value="lease" /><el-option label="其他" value="other" />
      </el-select>
      <el-button type="primary" @click="fetchList">搜索</el-button>
    </div>

    <el-table :data="items" stripe style="margin-top:var(--space-4)" v-loading="loading" empty-text="暂无合同数据">
      <el-table-column prop="title" label="合同标题" />
      <el-table-column label="类型" width="80"><template #default="{row}">{{ typeText(row.contract_type) }}</template></el-table-column>
      <el-table-column label="金额" width="120"><template #default="{row}">{{ row.amount ? '¥' + row.amount.toLocaleString() : '-' }}</template></el-table-column>
      <el-table-column label="状态" width="100"><template #default="{row}"><el-tag :type="statusTag(row.status)">{{ statusText(row.status) }}</el-tag></template></el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="240">
        <template #default="{row}">
          <el-button size="small" @click="$router.push(`/contracts/${row.id}`)">详情</el-button>
          <el-button v-if="row.status==='draft'||row.status==='voided'" size="small" type="primary" @click="$router.push(`/contracts/${row.id}/edit`)">编辑</el-button>
          <el-button v-if="row.status==='pending_approval' && row.creator_id===authStore.user?.id" size="small" type="warning" @click="handleWithdraw(row)">撤回</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="fetchList" style="margin-top:16px;justify-content:flex-end" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { contractApi } from '../api/contracts'
import { approvalApi } from '../api/approvals'
import { searchApi } from '../api/search'
import { statusTag, statusText, typeText } from '../composables/useStatus'

interface ContractItem {
  id: number
  title: string
  contract_type: string
  status: string
  amount: number | null
  created_at: string
  creator_id: number
}

interface PendingApproval {
  contract_id: number
  instance_id: number
}

const authStore = useAuthStore()
const items = ref<ContractItem[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const search = ref('')
const filterStatus = ref('')
const filterType = ref('')
const pdfAvailable = ref(true)  // optimistic until health check completes

onMounted(() => { fetchList(); checkHealth() })

async function checkHealth(): Promise<void> {
  try {
    const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
    const res = await fetch(`${baseURL}/health`)
    if (res.ok) {
      const data = await res.json()
      pdfAvailable.value = data.pdf_available !== false
    }
  } catch {
    // If health check fails, keep optimistic default (pdfAvailable=true)
  }
}

async function fetchList(): Promise<void> {
  loading.value = true
  try {
    if (search.value.trim()) {
      const params: Record<string, unknown> = { q: search.value.trim(), page: page.value, page_size: pageSize.value }
      if (filterStatus.value) params.status = filterStatus.value
      if (filterType.value) params.type = filterType.value
      const res = await searchApi.search(params)
      items.value = (res.data.items || []) as ContractItem[]
      total.value = (res.data.total || 0) as number
    } else {
      const params: Record<string, unknown> = { page: page.value, page_size: pageSize.value }
      if (filterStatus.value) params.status = filterStatus.value
      if (filterType.value) params.type = filterType.value
      const res = await contractApi.list(params)
      items.value = res.data.items as ContractItem[]
      total.value = res.data.total as number
    }
  } finally { loading.value = false }
}

async function handleExport(format: 'excel' | 'pdf'): Promise<void> {
  if (format === 'pdf' && !pdfAvailable.value) {
    ElMessage.warning('PDF 导出需要系统依赖（GTK3/Pango/Cairo），当前环境不支持。请使用 Excel 导出。')
    return
  }

  const params = new URLSearchParams()
  if (filterStatus.value) params.set('status', filterStatus.value)
  if (filterType.value) params.set('type', filterType.value)
  if (search.value.trim()) params.set('search', search.value.trim())

  const token = localStorage.getItem('token')
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
  const url = `${baseURL}/contracts/export/${format}?${params.toString()}`

  try {
    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: '导出失败' }))
      ElMessage.error(err.detail || '导出失败')
      return
    }
    const blob = await response.blob()
    const ext = format === 'excel' ? 'xlsx' : 'pdf'
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `contracts_${new Date().toISOString().slice(0, 10)}.${ext}`
    a.click()
    URL.revokeObjectURL(a.href)
    ElMessage.success(`已导出 ${format === 'excel' ? 'Excel' : 'PDF'}`)
  } catch {
    ElMessage.error('导出失败')
  }
}

async function handleWithdraw(row: ContractItem): Promise<void> {
  const confirmed = await ElMessageBox.confirm('确认撤回该审批？合同将回到草稿状态。', '确认撤回', { type: 'warning' }).catch(() => null)
  if (!confirmed) return
  const pendingRes = await approvalApi.pending()
  const myPending = ((pendingRes.data?.items || []) as PendingApproval[]).filter(p => p.contract_id === row.id)
  if (myPending.length > 0) {
    await approvalApi.withdraw(myPending[0].instance_id)
  } else {
    await ElMessage.warning('未找到可撤回的审批实例')
    return
  }
  ElMessage.success('已撤回')
  fetchList()
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-5); }
.page-header h2 { font-size: var(--font-size-2xl); font-weight: var(--font-weight-bold); color: var(--color-text); }
.toolbar { display: flex; gap: var(--space-3); flex-wrap: wrap; align-items: center; }
</style>
