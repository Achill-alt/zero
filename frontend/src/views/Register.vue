<template>
  <div class="register-page">
    <el-card class="register-card">
      <template #header><div class="card-title">新增用户</div></template>
      <el-form :model="form" label-width="100px">
        <el-form-item label="用户名"><el-input v-model="form.username" placeholder="请输入用户名" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" type="password" placeholder="默认 123456" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width:100%">
            <el-option label="经办人" value="handler" />
            <el-option label="审批人" value="approver" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="审批子角色" v-if="form.role === 'approver'">
          <el-select v-model="form.approver_role" style="width:100%" placeholder="选择审批角色">
            <el-option label="部门负责人" value="dept_manager" />
            <el-option label="法务" value="legal" />
            <el-option label="财务总监" value="finance_director" />
            <el-option label="总经理" value="ceo" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门"><el-input v-model="form.department" placeholder="所在部门" /></el-form-item>
        <el-form-item label="显示名"><el-input v-model="form.display_name" placeholder="用户显示名称" /></el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleRegister">创建用户</el-button>
          <el-button @click="$router.push('/admin/users')">返回用户管理</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '../api/auth'

const router = useRouter()
const loading = ref(false)
const form = reactive({
  username: '',
  password: '123456',
  role: 'handler' as string,
  approver_role: null as string | null,
  department: '',
  display_name: '',
})

async function handleRegister() {
  if (!form.username) { ElMessage.warning('请输入用户名'); return }
  loading.value = true
  try {
    await authApi.register({ ...form })
    ElMessage.success('用户创建成功')
    form.username = ''
    form.display_name = ''
    form.department = ''
  } finally { loading.value = false }
}
</script>

<style scoped>
.register-page { display: flex; align-items: center; justify-content: center; min-height: 100%; padding-top: 40px; }
.register-card { width: 480px; }
.register-card h2 { margin: 0; font-size: 18px; }
</style>
