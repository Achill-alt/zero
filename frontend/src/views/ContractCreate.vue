<template>
  <div class="contract-create">
    <h2>拟制合同</h2>
    <el-card style="margin-top:16px;max-width:900px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="选择模板">
          <el-select v-model="form.template_id" placeholder="选择合同模板（可选）" clearable @change="applyTemplate" style="width:100%">
            <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="合同标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入合同标题" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="合同类型" prop="contract_type">
              <el-select v-model="form.contract_type" placeholder="请选择" style="width:100%">
                <el-option label="采购合同" value="purchase" /><el-option label="销售合同" value="sales" />
                <el-option label="服务合同" value="service" /><el-option label="租赁合同" value="lease" /><el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="合同金额" prop="amount">
              <el-input-number v-model="form.amount" :min="0" :precision="2" style="width:100%" placeholder="请输入金额" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="甲方" prop="party_a"><el-input v-model="form.party_a" placeholder="甲方名称" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="乙方" prop="party_b"><el-input v-model="form.party_b" placeholder="乙方名称" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="开始日期" prop="start_date"><el-date-picker v-model="form.start_date" type="date" placeholder="选择日期" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="结束日期" prop="end_date"><el-date-picker v-model="form.end_date" type="date" placeholder="选择日期" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="合同内容" prop="content">
          <RichTextEditor v-model="form.content" placeholder="请输入合同内容..." @blur="formRef?.validateField('content')" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="saveDraft">保存草稿</el-button>
          <el-button type="success" :loading="submitting" @click="submitApproval">提交审批</el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { contractApi } from '../api/contracts'
import RichTextEditor from '../components/RichTextEditor.vue'

interface Template {
  id: number
  name: string
  title_template: string
  content_template: string
  contract_type?: string
}

interface ContractForm {
  title: string
  content: string
  contract_type: string
  amount: number | null
  party_a: string
  party_b: string
  start_date: string | null
  end_date: string | null
  template_id: number | null
}

const router = useRouter()
const formRef = ref<FormInstance>()
const saving = ref(false)
const submitting = ref(false)
const templates = ref<Template[]>([])

const form: ContractForm = reactive({
  title: '', content: '', contract_type: '', amount: null,
  party_a: '', party_b: '', start_date: null, end_date: null, template_id: null,
})

const rules: FormRules = {
  title: [{ required: true, message: '请输入合同标题', trigger: 'blur' }],
  contract_type: [{ required: true, message: '请选择合同类型', trigger: 'change' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }],
}

onMounted(async () => {
  const res = await contractApi.templates()
  templates.value = res.data.items as Template[]
})

function applyTemplate(id: number | null): void {
  const tpl = templates.value.find(t => t.id === id)
  if (tpl) {
    form.title = tpl.title_template
    form.content = tpl.content_template
    if (tpl.contract_type) form.contract_type = tpl.contract_type
  }
}

function fmtDate(d: string | Date | null): string {
  if (!d) return ''
  const dt = new Date(d as string)
  return dt.toISOString().split('T')[0]
}

async function saveDraft(): Promise<void> {
  const valid = await formRef.value!.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const res = await contractApi.create({ ...form, start_date: fmtDate(form.start_date), end_date: fmtDate(form.end_date) })
    ElMessage.success('草稿已保存')
    router.push(`/contracts/${res.data.id}`)
  } finally { saving.value = false }
}

async function submitApproval(): Promise<void> {
  const valid = await formRef.value!.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const res = await contractApi.create({ ...form, start_date: fmtDate(form.start_date), end_date: fmtDate(form.end_date) })
    await contractApi.submit(res.data.id)
    ElMessage.success('已提交审批')
    router.push(`/contracts/${res.data.id}`)
  } finally { submitting.value = false }
}
</script>
