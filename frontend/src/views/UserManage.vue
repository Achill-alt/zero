<template>
  <div class="user-manage">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="showRegister = true"><el-icon><Plus /></el-icon> 新增用户</el-button>
    </div>
    <el-table :data="users" stripe style="margin-top:var(--space-4)" v-loading="loading">
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="display_name" label="显示名" />
      <el-table-column label="角色" width="100"><template #default="{row}"><el-tag>{{ roleText(row.role) }}</el-tag></template></el-table-column>
      <el-table-column prop="department" label="部门" />
      <el-table-column label="审批角色" width="120"><template #default="{row}">{{ row.approver_role || '-' }}</template></el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{row}">
          <el-switch :model-value="row.is_active" :active-value="true" :inactive-value="false"
            @change="toggleUser(row, $event)" />
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showRegister" title="新增用户" width="500px">
      <el-form :model="regForm" label-width="100px">
        <el-form-item label="用户名"><el-input v-model="regForm.username" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="regForm.password" type="password" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="regForm.role" style="width:100%">
            <el-option label="经办人" value="handler" /><el-option label="审批人" value="approver" /><el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="审批子角色" v-if="regForm.role==='approver'">
          <el-select v-model="regForm.approver_role" style="width:100%">
            <el-option label="部门负责人" value="dept_manager" /><el-option label="法务" value="legal" />
            <el-option label="财务总监" value="finance_director" /><el-option label="总经理" value="ceo" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门"><el-input v-model="regForm.department" /></el-form-item>
        <el-form-item label="显示名"><el-input v-model="regForm.display_name" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRegister = false">取消</el-button>
        <el-button type="primary" @click="handleRegister">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { authApi } from '../api/auth'
import { adminApi } from '../api/admin'

interface User {
  id: number
  username: string
  display_name: string
  role: string
  department: string
  approver_role: string | null
  is_active: boolean
}

interface RegForm {
  username: string
  password: string
  role: string
  approver_role: string | null
  department: string
  display_name: string
}

const users = ref<User[]>([])
const loading = ref(false)
const showRegister = ref(false)
const regForm = ref<RegForm>({ username: '', password: '123456', role: 'handler', approver_role: null, department: '', display_name: '' })

onMounted(async () => {
  loading.value = true
  try {
    const res = await adminApi.users({ page: 1, page_size: 100 })
    users.value = res.data.items as User[]
  } finally { loading.value = false }
})

async function handleRegister(): Promise<void> {
  if (!regForm.value.username || regForm.value.username.length < 3) {
    ElMessage.warning('用户名至少需要3个字符')
    return
  }
  if (!regForm.value.password || regForm.value.password.length < 6) {
    ElMessage.warning('密码至少需要6个字符')
    return
  }
  try {
    await authApi.register(regForm.value as Record<string, unknown>)
    ElMessage.success('用户已创建')
    showRegister.value = false
    regForm.value = { username: '', password: '123456', role: 'handler', approver_role: null, department: '', display_name: '' }
    const res = await adminApi.users({ page: 1, page_size: 100 })
    users.value = res.data.items as User[]
  } catch {
    // 错误已由拦截器统一提示，这里只阻止异常传播
  }
}

async function toggleUser(row: User, value: boolean): Promise<void> {
  await adminApi.updateUser(row.id, { is_active: value })
  ElMessage.success(value ? '用户已启用' : '用户已禁用')
  row.is_active = value
}

function roleText(r: string): string {
  const map: Record<string, string> = { admin: '管理员', handler: '经办人', approver: '审批人' }
  return map[r] || r
}
</script>
