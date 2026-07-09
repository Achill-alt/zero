<template>
  <header class="navbar">
    <div class="navbar-left">
      <h1 class="logo">📋 企业合同管理系统</h1>
    </div>

    <div class="navbar-right">
      <!-- Notification bell -->
      <el-popover ref="popoverRef" placement="bottom-end" :width="380" trigger="click" @show="fetchNotifications" popper-class="notif-popover">
        <template #reference>
          <div class="bell-wrapper">
            <el-badge :value="unreadCount" :max="99" :hidden="unreadCount === 0">
              <button class="bell-btn" aria-label="通知中心">
                <el-icon :size="20"><Bell /></el-icon>
              </button>
            </el-badge>
          </div>
        </template>
        <div v-if="recentNotifs.length > 0">
          <div
            v-for="n in recentNotifs"
            :key="n.id"
            class="notif-item"
            :class="{ unread: !n.is_read }"
            @click="handleNotifClick(n)"
          >
            <div class="notif-dot" :class="n.is_read ? 'read' : 'unread'"></div>
            <div class="notif-body">
              <div class="notif-title">{{ n.title }}</div>
              <div class="notif-content">{{ n.content }}</div>
              <div class="notif-time">{{ n.created_at }}</div>
            </div>
          </div>
          <div class="notif-footer">
            <el-button size="small" text @click="handleMarkAllRead">全部已读</el-button>
            <el-button size="small" text type="primary" @click="goToList">查看全部</el-button>
          </div>
        </div>
        <div v-else class="notif-empty">
          <el-icon :size="32" color="#c0c4cc"><Bell /></el-icon>
          <p>暂无通知</p>
        </div>
      </el-popover>

      <div class="user-info">
        <span class="username">{{ authStore.user?.display_name || authStore.user?.username }}</span>
        <el-tag size="small" :type="roleTagType" effect="plain">{{ roleText }}</el-tag>
      </div>

      <el-button class="logout-btn" @click="handleLogout">
        <el-icon><SwitchButton /></el-icon>
        <span>退出</span>
      </el-button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { notificationApi } from '../api/notifications'

interface Notification {
  id: number
  title: string
  content: string
  is_read: boolean
  created_at: string
  related_id?: number
}

const router = useRouter()
const authStore = useAuthStore()

const popoverRef = ref<any>(null)

const roleText = computed<string>(() => {
  const map: Record<string, string> = { admin: '管理员', handler: '经办人', approver: '审批人' }
  return map[authStore.user?.role || ''] || authStore.user?.role || ''
})

const roleTagType = computed<string>(() => {
  const map: Record<string, string> = { admin: 'danger', handler: 'primary', approver: 'success' }
  return map[authStore.user?.role || ''] || 'info'
})

function handleLogout(): void {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  popoverRef.value?.hide()
  setTimeout(() => {
    authStore.logout()
    router.push('/login')
  }, 150)
}

// Notification state
const unreadCount = ref(0)
const recentNotifs = ref<Notification[]>([])
let pollTimer: ReturnType<typeof setInterval> | null = null

async function fetchUnreadCount(): Promise<void> {
  try {
    const res = await notificationApi.unreadCount()
    unreadCount.value = res.data.count
  } catch { /* ignore */ }
}

async function fetchNotifications(): Promise<void> {
  try {
    const res = await notificationApi.list(1, 5)
    recentNotifs.value = res.data.items || []
  } catch { /* ignore */ }
}

async function handleNotifClick(n: Notification): Promise<void> {
  if (!n.is_read) {
    try {
      await notificationApi.markRead(n.id)
      n.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch { /* ignore */ }
  }
  if (n.related_id) {
    router.push(`/contracts/${n.related_id}`)
  }
}

async function handleMarkAllRead(): Promise<void> {
  try {
    await notificationApi.markAllRead()
    recentNotifs.value.forEach(n => n.is_read = true)
    unreadCount.value = 0
  } catch { /* ignore */ }
}

function goToList(): void {
  router.push('/notifications')
}

onMounted(() => {
  fetchUnreadCount()
  pollTimer = setInterval(fetchUnreadCount, 30000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
/* ── Navbar ────────────────────────────────────────────────────── */
.navbar {
  height: var(--navbar-height);
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-6);
  box-shadow: var(--shadow-xs);
  position: sticky;
  top: 0;
  z-index: var(--z-navbar);
}

.navbar-left {
  display: flex;
  align-items: center;
}

.logo {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
  letter-spacing: 0.02em;
}

/* ── Right section ─────────────────────────────────────────────── */
.navbar-right {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

/* ── Bell button ───────────────────────────────────────────────── */
.bell-wrapper {
  display: flex;
  align-items: center;
}
.bell-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--space-2);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}
.bell-btn:hover {
  background: var(--color-bg-hover);
  color: var(--color-primary);
}

/* ── User info ─────────────────────────────────────────────────── */
.user-info {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.username {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
}

/* ── Logout button ─────────────────────────────────────────────── */
.logout-btn {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  border: 1px solid var(--color-border);
  background: var(--color-bg-card);
  color: var(--color-text-secondary);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.logout-btn:hover {
  color: var(--color-danger);
  border-color: var(--color-danger);
  background: var(--color-danger-light);
}

/* ── Notification popover ──────────────────────────────────────── */
.notif-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-2);
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
}
.notif-item:hover { background: var(--color-bg-hover); }
.notif-item.unread { background: var(--color-primary-bg); }
.notif-dot {
  width: 8px; height: 8px; border-radius: 50%; margin-top: 6px; flex-shrink: 0;
}
.notif-dot.unread { background: var(--color-primary); }
.notif-dot.read { background: transparent; }
.notif-body { flex: 1; min-width: 0; }
.notif-title { font-size: var(--font-size-sm); font-weight: var(--font-weight-semibold); color: var(--color-text); }
.notif-content { font-size: var(--font-size-xs); color: var(--color-text-secondary); margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.notif-time { font-size: 10px; color: var(--color-text-tertiary); margin-top: 4px; }
.notif-footer {
  display: flex;
  justify-content: space-between;
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-border-light);
  margin-top: var(--space-1);
}
.notif-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-6) 0;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
}
</style>
