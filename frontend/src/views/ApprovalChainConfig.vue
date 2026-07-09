<template>
  <div class="approval-chain-config">
    <div class="page-header">
      <h2>审批链配置</h2>
      <el-button type="primary" @click="showCreate = true"><el-icon><Plus /></el-icon> 新建审批链</el-button>
    </div>

    <el-row :gutter="20" style="margin-top:16px">
      <el-col :span="12" v-for="chain in chains" :key="chain.id">
        <el-card shadow="hover">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>{{ chain.name }}</span>
              <el-switch v-model="chain.is_active" @change="toggleChain(chain, $event)" />
            </div>
          </template>
          <p><strong>优先级：</strong>{{ chain.priority }}</p>
          <p><strong>条件：</strong>{{ JSON.stringify(chain.conditions) }}</p>
          <p><strong>步骤：</strong></p>
          <ol>
            <li v-for="(step, idx) in chain.steps" :key="idx">{{ step.name }} → {{ step.role }}（{{ step.timeout_hours }}h）</li>
          </ol>
          <div style="margin-top:12px">
            <el-button size="small" @click="editChain(chain)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteChain(chain.id)">删除</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showCreate" title="新建/编辑审批链" width="700px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="优先级"><el-input-number v-model="form.priority" :min="0" /></el-form-item>
        <el-form-item label="触发条件-合同类型">
          <el-select v-model="form.conditions.contract_type" multiple placeholder="不限" style="width:100%">
            <el-option label="采购" value="purchase" /><el-option label="销售" value="sales" />
            <el-option label="服务" value="service" /><el-option label="租赁" value="lease" /><el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="最低金额"><el-input-number v-model="form.conditions.amount_min" :min="0" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="最高金额"><el-input-number v-model="form.conditions.amount_max" :min="0" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="审批步骤">
          <div v-for="(step, idx) in form.steps" :key="idx" style="margin-bottom:8px;padding:8px;border:1px solid #e4e7ed;border-radius:4px">
            <el-row :gutter="8">
              <el-col :span="8"><el-input v-model="step.name" placeholder="步骤名称" /></el-col>
              <el-col :span="6">
                <el-select v-model="step.role" placeholder="审批角色" style="width:100%">
                  <el-option label="部门负责人" value="dept_manager" /><el-option label="法务" value="legal" />
                  <el-option label="财务总监" value="finance_director" /><el-option label="总经理" value="ceo" />
                </el-select>
              </el-col>
              <el-col :span="6"><el-input-number v-model="step.timeout_hours" :min="1" placeholder="超时(h)" style="width:100%" /></el-col>
              <el-col :span="4"><el-button type="danger" @click="removeStep(idx)">删除</el-button></el-col>
            </el-row>
          </div>
          <el-button type="primary" plain @click="addStep">+ 添加步骤</el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { approvalApi } from '../api/approvals'

interface ApprovalChain {
  id: number
  name: string
  priority: number
  is_active: boolean
  conditions: ChainConditions
  steps: ChainStep[]
}

interface ChainConditions {
  contract_type: string[]
  amount_min: number | null
  amount_max: number | null
}

interface ChainStep {
  name: string
  role: string
  timeout_hours: number
}

interface ChainForm {
  name: string
  priority: number
  conditions: ChainConditions
  steps: ChainStep[]
}

const chains = ref<ApprovalChain[]>([])
const showCreate = ref(false)
const editingId = ref<number | null>(null)
const form = ref<ChainForm>(getDefaultForm())

function getDefaultForm(): ChainForm {
  return {
    name: '', priority: 0,
    conditions: { contract_type: [], amount_min: null, amount_max: null },
    steps: [{ name: '部门审批', role: 'dept_manager', timeout_hours: 24 }],
  }
}

onMounted(async () => {
  const res = await approvalApi.chainList()
  chains.value = res.data as ApprovalChain[]
})

function addStep(): void { form.value.steps.push({ name: '', role: 'dept_manager', timeout_hours: 24 }) }
function removeStep(idx: number): void { form.value.steps.splice(idx, 1) }

function editChain(chain: ApprovalChain): void {
  editingId.value = chain.id
  form.value = {
    name: chain.name, priority: chain.priority,
    conditions: { ...chain.conditions },
    steps: chain.steps.map(s => ({ ...s })),
  }
  showCreate.value = true
}

async function handleSave(): Promise<void> {
  const conditions: Record<string, unknown> = {}
  if (form.value.conditions.contract_type && form.value.conditions.contract_type.length > 0)
    conditions.contract_type = form.value.conditions.contract_type
  if (form.value.conditions.amount_min) conditions.amount_min = form.value.conditions.amount_min
  if (form.value.conditions.amount_max) conditions.amount_max = form.value.conditions.amount_max

  const data = { ...form.value, conditions } as Record<string, unknown>
  if (editingId.value) {
    await approvalApi.chainUpdate(editingId.value, data)
  } else {
    await approvalApi.chainCreate(data)
  }
  ElMessage.success('保存成功')
  showCreate.value = false
  editingId.value = null
  form.value = getDefaultForm()
  const res = await approvalApi.chainList()
  chains.value = res.data as ApprovalChain[]
}

async function toggleChain(chain: ApprovalChain, value: boolean): Promise<void> {
  try {
    await approvalApi.chainUpdate(chain.id, { is_active: value } as Record<string, unknown>)
    ElMessage.success(value ? '已启用' : '已禁用')
  } catch { chain.is_active = !value }
}

async function deleteChain(id: number): Promise<void> {
  const confirmed = await ElMessageBox.confirm('确认删除？', '删除审批链', { type: 'warning' }).catch(() => null)
  if (!confirmed) return
  await approvalApi.chainDelete(id)
  ElMessage.success('已删除')
  chains.value = chains.value.filter(c => c.id !== id)
}
</script>
