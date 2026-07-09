<template>
  <div class="template-manage">
    <div class="page-header">
      <h2>模板管理</h2>
      <el-button type="primary" @click="showCreate = true">
        <el-icon><Plus /></el-icon> 新建模板
      </el-button>
    </div>

    <el-row :gutter="20" style="margin-top:var(--space-4)">
      <el-col :span="8" v-for="t in templates" :key="t.id">
        <el-card shadow="hover">
          <h3>{{ t.name }}</h3>
          <div class="template-meta">
            <span><el-icon><Collection /></el-icon> {{ typeText(t.contract_type) }}</span>
            <span>{{ t.created_at }}</span>
          </div>
          <div class="template-actions">
            <el-button size="small" @click="editTemplate(t)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteTemplate(t.id)">删除</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="templates.length === 0" description="暂无模板">
      <el-button type="primary" @click="showCreate = true">新建模板</el-button>
    </el-empty>

    <el-dialog v-model="showCreate" :title="editingId ? '编辑模板' : '新建模板'" width="600px" destroy-on-close>
      <el-form :model="newTpl" label-width="100px">
        <el-form-item label="模板名称"><el-input v-model="newTpl.name" placeholder="例如：标准采购合同" /></el-form-item>
        <el-form-item label="标题模板"><el-input v-model="newTpl.title_template" placeholder="例如：采购合同 - {供应商名称}" /></el-form-item>
        <el-form-item label="适用类型">
          <el-select v-model="newTpl.contract_type" style="width:100%">
            <el-option label="采购" value="purchase" /><el-option label="销售" value="sales" />
            <el-option label="服务" value="service" /><el-option label="租赁" value="lease" /><el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容模板"><el-input v-model="newTpl.content_template" type="textarea" :rows="8" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminApi } from '../api/admin'
import { contractApi } from '../api/contracts'
import { typeText } from '../composables/useStatus'

interface Template {
  id: number
  name: string
  title_template: string
  content_template: string
  contract_type: string
  created_at: string
}

interface NewTemplateForm {
  name: string
  title_template: string
  content_template: string
  contract_type: string
}

const templates = ref<Template[]>([])
const showCreate = ref(false)
const editingId = ref<number | null>(null)
const newTpl = ref<NewTemplateForm>({ name: '', title_template: '', content_template: '', contract_type: 'purchase' })

onMounted(async () => {
  const res = await contractApi.templates()
  templates.value = res.data.items as Template[]
})

async function handleCreate(): Promise<void> {
  if (editingId.value) {
    await adminApi.updateTemplate(editingId.value, newTpl.value as Record<string, unknown>)
    ElMessage.success('模板已更新')
  } else {
    await adminApi.templates(newTpl.value as Record<string, unknown>)
    ElMessage.success('模板已创建')
  }
  showCreate.value = false
  editingId.value = null
  newTpl.value = { name: '', title_template: '', content_template: '', contract_type: 'purchase' }
  const res = await contractApi.templates()
  templates.value = res.data.items as Template[]
}

function editTemplate(t: Template): void {
  editingId.value = t.id
  newTpl.value = {
    name: t.name,
    title_template: t.title_template,
    content_template: t.content_template,
    contract_type: t.contract_type,
  }
  showCreate.value = true
}

async function deleteTemplate(id: number): Promise<void> {
  const confirmed = await ElMessageBox.confirm('确认删除该模板？', '删除模板', { type: 'warning' }).catch(() => null)
  if (!confirmed) return
  await adminApi.deleteTemplate(id)
  ElMessage.success('已删除')
  templates.value = templates.value.filter(t => t.id !== id)
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-6); }
.page-header h2 { font-size: var(--font-size-2xl); font-weight: var(--font-weight-bold); color: var(--color-text); }

.template-meta {
  display: flex; flex-direction: column; gap: var(--space-1);
  margin-top: var(--space-3);
  font-size: var(--font-size-sm); color: var(--color-text-secondary);
}
.template-meta span { display: flex; align-items: center; gap: var(--space-1); }

.template-actions { display: flex; gap: var(--space-2); margin-top: var(--space-4); padding-top: var(--space-3); border-top: 1px solid var(--color-border-light); }
</style>
