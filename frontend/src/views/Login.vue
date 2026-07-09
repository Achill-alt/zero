<template>
  <div class="login-page">
    <!-- Background decoration -->
    <div class="login-bg">
      <div class="bg-shape bg-shape-1"></div>
      <div class="bg-shape bg-shape-2"></div>
      <div class="bg-shape bg-shape-3"></div>
    </div>

    <div class="login-card">
      <div class="login-header">
        <div class="login-icon">📋</div>
        <h1>企业合同管理系统</h1>
        <p class="login-subtitle">Enterprise Contract Management</p>
      </div>

      <el-form
        :model="form"
        :rules="rules"
        ref="formRef"
        label-position="top"
        class="login-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            size="large"
            class="login-btn"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-hints">
        <p><strong>演示账号：</strong></p>
        <p>admin / admin123（管理员）</p>
        <p>handler1 / 123456（经办人）</p>
        <p>approver1 / 123456（审批人）</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({ username: '', password: '' })
const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin(): Promise<void> {
  const valid = await formRef.value!.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } finally { loading.value = false }
}
</script>

<style scoped>
/* ── Page ──────────────────────────────────────────────────────── */
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 30%, #3b6df0 70%, #6c8ef5 100%);
}

/* ── Background shapes ──────────────────────────────────────────── */
.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.bg-shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.08;
  background: #fff;
}
.bg-shape-1 {
  width: 600px; height: 600px;
  top: -200px; right: -150px;
}
.bg-shape-2 {
  width: 400px; height: 400px;
  bottom: -100px; left: -100px;
}
.bg-shape-3 {
  width: 200px; height: 200px;
  top: 40%; left: 60%;
}

/* ── Card ──────────────────────────────────────────────────────── */
.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  padding: var(--space-10) var(--space-10) var(--space-8);
  background: var(--color-bg-card);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
}

/* ── Header ────────────────────────────────────────────────────── */
.login-header {
  text-align: center;
  margin-bottom: var(--space-8);
}
.login-icon {
  font-size: 48px;
  margin-bottom: var(--space-3);
}
.login-header h1 {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
  letter-spacing: 0.03em;
}
.login-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  margin-top: var(--space-1);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* ── Form ──────────────────────────────────────────────────────── */
.login-form {
  margin-top: var(--space-6);
}
.login-btn {
  width: 100%;
  height: 44px;
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.1em;
  border-radius: var(--radius-md);
}

/* ── Hints ─────────────────────────────────────────────────────── */
.login-hints {
  margin-top: var(--space-6);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border-light);
  text-align: center;
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  line-height: var(--line-height-relaxed);
}
.login-hints strong {
  color: var(--color-text-secondary);
}
</style>
