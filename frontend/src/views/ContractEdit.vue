<template>
  <div class="contract-edit" v-loading="loading">
    <h2>编辑合同</h2>
    <el-card style="margin-top:16px;max-width:900px">
      <el-form v-if="form" :model="form" ref="formRef" label-width="100px">
        <el-form-item label="合同标题" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="合同类型">
              <el-select v-model="form.contract_type" style="width:100%">
                <el-option label="采购" value="purchase" /><el-option label="销售" value="sales" />
                <el-option label="服务" value="service" /><el-option label="租赁" value="lease" /><el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="合同金额">
              <el-input-number v-model="form.amount" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="甲方"><el-input v-model="form.party_a" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="乙方"><el-input v-model="form.party_b" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="开始日期"><el-date-picker v-model="form.start_date" type="date" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="结束日期"><el-date-picker v-model="form.end_date" type="date" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="合同内容">
          <el-input v-model="form.content" type="textarea" :rows="10" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { contractApi } from '../api/contracts'

interface EditForm {
  title: string
  content: string
  contract_type: string
  amount: number | null
  party_a: string
  party_b: string
  start_date: string
  end_date: string
}

const route = useRoute()
const router = useRouter()
const form = ref<EditForm | null>(null)
const saving = ref(false)
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const res = await contractApi.get(route.params.id as string)
    const c = res.data
    form.value = {
      title: c.title, content: c.content, contract_type: c.contract_type,
      amount: c.amount, party_a: c.party_a, party_b: c.party_b,
      start_date: c.start_date, end_date: c.end_date,
    }
  } finally { loading.value = false }
})

async function handleSave(): Promise<void> {
  saving.value = true
  try {
    const data = { ...form.value! } as Record<string, unknown>
    if (data.start_date) data.start_date = new Date(data.start_date as string).toISOString().split('T')[0]
    if (data.end_date) data.end_date = new Date(data.end_date as string).toISOString().split('T')[0]
    await contractApi.update(route.params.id as string, data)
    ElMessage.success('保存成功')
    router.push(`/contracts/${route.params.id}`)
  } finally { saving.value = false }
}
</script>
