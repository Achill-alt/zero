<template>
  <div class="contract-detail" v-loading="loading">
    <div class="page-header">
      <h2>合同详情</h2>
      <el-button @click="$router.back()">返回</el-button>
    </div>
    <template v-if="contract">
      <el-card style="margin-top:var(--space-4)">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="合同标题">{{ contract.title }}</el-descriptions-item>
          <el-descriptions-item label="合同类型">{{ typeText(contract.contract_type) }}</el-descriptions-item>
          <el-descriptions-item label="合同金额">{{ contract.amount ? '¥' + contract.amount.toLocaleString() : '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态"><el-tag :type="statusTag(contract.status)">{{ statusText(contract.status) }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="甲方">{{ contract.party_a }}</el-descriptions-item>
          <el-descriptions-item label="乙方">{{ contract.party_b }}</el-descriptions-item>
          <el-descriptions-item label="开始日期">{{ contract.start_date }}</el-descriptions-item>
          <el-descriptions-item label="结束日期">{{ contract.end_date }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ contract.created_at }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ contract.updated_at }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card header="合同内容" style="margin-top:16px">
        <div v-html="contract.content || '(无内容)'" style="min-height:100px;white-space:pre-wrap" />
      </el-card>

      <el-card header="附件" style="margin-top:16px">
        <template v-if="authStore.isHandler || authStore.isAdmin">
          <el-upload
            :action="uploadAction"
            :headers="uploadHeaders"
            :before-upload="beforeUpload"
            :on-success="onUploadSuccess"
            :on-error="onUploadError"
            :show-file-list="false"
            drag
            accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.gif,.txt"
          >
            <el-icon style="font-size:24px"><UploadFilled /></el-icon>
            <div style="margin-top:8px">拖拽文件到此处或点击上传</div>
            <template #tip>
              <div style="margin-top:4px;font-size:12px;color:#909399">
                支持 PDF、Word、Excel、图片、TXT，单文件最大 10MB
              </div>
            </template>
          </el-upload>
        </template>
        <el-table v-if="attachments.length > 0" :data="attachments" style="margin-top:12px" size="small">
          <el-table-column prop="filename" label="文件名" min-width="200" />
          <el-table-column label="大小" width="100">
            <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
          </el-table-column>
          <el-table-column prop="created_at" label="上传时间" width="170" />
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="handleDownload(row.id, row.filename)">下载</el-button>
              <el-button v-if="authStore.isHandler || authStore.isAdmin" size="small" type="danger" link @click="handleDeleteAttachment(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-else style="color:#909399;font-size:13px;margin-top:8px">暂无附件</div>
      </el-card>

      <el-card v-if="approvalHistory.length > 0" header="审批历史" style="margin-top:16px">
        <el-timeline>
          <el-timeline-item v-for="(result, idx) in allStepResults" :key="idx"
            :type="result.action === 'approve' ? 'success' : result.action === 'reject' ? 'danger' : 'info'"
            :timestamp="result.acted_at">
            <p><strong>{{ result.step_name }}</strong> — {{ result.user_name }}（{{ result.action === 'approve' ? '通过' : result.action === 'reject' ? '驳回' : '待审批' }}）</p>
            <p v-if="result.comment" style="color:#909399">{{ result.comment }}</p>
          </el-timeline-item>
        </el-timeline>
      </el-card>

      <div class="actions">
        <el-button v-if="contract.status==='draft'" type="primary" @click="$router.push(`/contracts/${contract.id}/edit`)">编辑</el-button>
        <el-button v-if="contract.status==='draft'" type="success" @click="handleSubmit">提交审批</el-button>
        <el-button v-if="contract.status==='draft'" type="danger" @click="handleVoid">作废</el-button>
        <el-button v-if="canWithdraw" type="warning" @click="handleWithdraw">撤回审批</el-button>
        <el-button v-if="contract.status==='approved'" type="success" @click="handleArchive">归档</el-button>
        <el-button v-if="canApprove" type="success" @click="handleApprove">通过</el-button>
        <el-button v-if="canApprove" type="danger" @click="handleReject">驳回</el-button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { contractApi } from '../api/contracts'
import { approvalApi } from '../api/approvals'
import { attachmentApi } from '../api/attachments'
import api from '../api'
import { statusTag, statusText, typeText } from '../composables/useStatus'

interface Contract {
  id: number
  title: string
  contract_type: string
  status: string
  amount: number | null
  party_a: string
  party_b: string
  start_date: string
  end_date: string
  created_at: string
  updated_at: string
  content: string
  creator_id: number
}

interface ApprovalInstance {
  instance_id: number
  status: string
  step_results?: StepResult[]
}

interface StepResult {
  step_name: string
  user_name: string
  action: string
  comment?: string
  acted_at: string
}

interface PendingItem {
  contract_id: number
  instance_id: number
}

interface Attachment {
  id: number
  filename: string
  file_size: number
  created_at: string
}

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const contract = ref<Contract | null>(null)
const approvalHistory = ref<ApprovalInstance[]>([])
const loading = ref(false)
const userPending = ref<PendingItem[]>([])
const attachments = ref<Attachment[]>([])
const uploading = ref(false)

const allStepResults = computed<StepResult[]>(() => {
  const results: StepResult[] = []
  for (const inst of approvalHistory.value) {
    for (const r of (inst.step_results || [])) {
      results.push(r)
    }
  }
  return results
})

const canApprove = computed<boolean>(() => {
  if (!contract.value || contract.value.status !== 'pending_approval') return false
  if (!authStore.isApprover && !authStore.isAdmin) return false
  return userPending.value.some(p => p.contract_id === contract.value!.id)
})

const canWithdraw = computed<boolean>(() => {
  if (!contract.value || contract.value.status !== 'pending_approval') return false
  if (!authStore.user) return false
  if (contract.value.creator_id !== authStore.user.id) return false
  return approvalHistory.value.some(h => h.status === 'in_progress')
})

const uploadAction = computed<string>(() => {
  const base: string = api.defaults.baseURL || '/api/v1'
  return `${base}/contracts/${route.params.id}/attachments`
})
const uploadHeaders = computed<Record<string, string>>(() => ({
  Authorization: `Bearer ${authStore.token}`,
}))

function formatSize(bytes: number | null): string {
  if (bytes == null) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function beforeUpload(file: File): boolean {
  const allowed = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg', '.gif', '.txt']
  const ext = '.' + file.name.split('.').pop()!.toLowerCase()
  if (!allowed.includes(ext)) {
    ElMessage.error(`不支持的文件类型: ${ext}`)
    return false
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 10MB')
    return false
  }
  return true
}

function onUploadSuccess(): void {
  ElMessage.success('上传成功')
  fetchAttachments()
}

function onUploadError(err: any): void {
  const msg = err?.response?.data?.detail || err?.message || '上传失败'
  ElMessage.error(msg)
}

async function fetchAttachments(): Promise<void> {
  try {
    const res = await attachmentApi.list(route.params.id as string)
    attachments.value = (res.data || []) as Attachment[]
  } catch { /* ignore */ }
}

async function handleDownload(id: number, filename: string): Promise<void> {
  try {
    const res = await api.get(`/attachments/${id}/download`, { responseType: 'blob' })
    const blob = res instanceof Blob ? res : new Blob([res as unknown as BlobPart])
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('下载失败')
  }
}

async function handleDeleteAttachment(id: number): Promise<void> {
  const confirmed = await ElMessageBox.confirm('确认删除该附件？', '确认删除', { type: 'warning' }).catch(() => null)
  if (!confirmed) return
  try {
    await attachmentApi.delete(id)
    ElMessage.success('已删除')
    fetchAttachments()
  } catch { /* ignore */ }
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await contractApi.get(route.params.id as string)
    contract.value = res.data as Contract
    approvalHistory.value = res.data.approval_history || []
    if (authStore.isApprover || authStore.isAdmin) {
      const pendingRes = await approvalApi.pending()
      userPending.value = (pendingRes.data?.items || []) as PendingItem[]
    }
    fetchAttachments()
  } finally { loading.value = false }
})

async function handleSubmit(): Promise<void> {
  await contractApi.submit(contract.value!.id)
  ElMessage.success('已提交审批')
  const res = await contractApi.get(contract.value!.id)
  contract.value = res.data as Contract
  approvalHistory.value = res.data.approval_history || []
}

async function handleApprove(): Promise<void> {
  const { value: comment } = await ElMessageBox.prompt('请输入审批意见（可选）', '审批通过', {
    confirmButtonText: '通过', cancelButtonText: '取消', inputPlaceholder: '审批意见',
  }).catch(() => ({ value: undefined }))
  if (comment === null || comment === undefined) return
  const activeInst = approvalHistory.value.find(h => h.status === 'in_progress')
  if (!activeInst) { ElMessage.error('未找到进行中的审批实例'); return }
  await approvalApi.approve(activeInst.instance_id, comment || '')
  ElMessage.success('审批通过')
  const res = await contractApi.get(contract.value!.id)
  contract.value = res.data as Contract
  approvalHistory.value = res.data.approval_history || []
}

async function handleReject(): Promise<void> {
  const { value: comment } = await ElMessageBox.prompt('请输入驳回理由', '驳回审批', {
    confirmButtonText: '驳回', cancelButtonText: '取消', inputPlaceholder: '驳回理由（必填）',
  }).catch(() => ({ value: undefined }))
  if (!comment) { ElMessage.warning('请输入驳回理由'); return }
  const activeInst = approvalHistory.value.find(h => h.status === 'in_progress')
  if (!activeInst) { ElMessage.error('未找到进行中的审批实例'); return }
  await approvalApi.reject(activeInst.instance_id, comment)
  ElMessage.success('已驳回')
  const res = await contractApi.get(contract.value!.id)
  contract.value = res.data as Contract
  approvalHistory.value = res.data.approval_history || []
}

async function handleArchive(): Promise<void> {
  await contractApi.archive(contract.value!.id)
  ElMessage.success('已归档')
  contract.value!.status = 'archived'
}

async function handleWithdraw(): Promise<void> {
  const confirmed = await ElMessageBox.confirm('确认撤回该审批？合同将回到草稿状态。', '确认撤回', { type: 'warning' }).catch(() => null)
  if (!confirmed) return
  const activeInst = approvalHistory.value.find(h => h.status === 'in_progress')
  if (!activeInst) { ElMessage.error('未找到进行中的审批实例'); return }
  await approvalApi.withdraw(activeInst.instance_id)
  ElMessage.success('已撤回')
  const res = await contractApi.get(contract.value!.id)
  contract.value = res.data as Contract
  approvalHistory.value = res.data.approval_history || []
}

async function handleVoid(): Promise<void> {
  const confirmed = await ElMessageBox.confirm('确认作废该合同？此操作不可撤销。', '确认作废', { type: 'warning' }).catch(() => null)
  if (!confirmed) return
  await contractApi.void(contract.value!.id)
  ElMessage.success('已作废')
  contract.value!.status = 'voided'
}

</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-5); }
.page-header h2 { font-size: var(--font-size-2xl); font-weight: var(--font-weight-bold); color: var(--color-text); }
.actions { display: flex; gap: var(--space-3); flex-wrap: wrap; margin-top: var(--space-4); }
</style>