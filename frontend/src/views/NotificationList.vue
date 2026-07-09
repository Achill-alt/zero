<template>
  <div class="notification-page">
    <div class="page-header">
      <h2>通知中心</h2>
      <el-button v-if="total > 0" size="small" text type="primary" @click="handleMarkAllRead">
        全部标记已读
      </el-button>
    </div>

    <div v-loading="loading">
      <template v-if="items.length > 0">
        <div
          v-for="n in items"
          :key="n.id"
          class="notif-card"
          :class="{ unread: !n.is_read }"
          @click="handleClick(n)"
        >
          <div class="notif-indicator" :class="n.is_read ? 'read' : 'unread'"></div>
          <div class="notif-info">
            <div class="notif-title">
              {{ n.title }}
              <el-tag v-if="!n.is_read" size="small" type="primary" effect="dark" round>新</el-tag>
            </div>
            <div class="notif-content">{{ n.content }}</div>
            <div class="notif-time">{{ n.created_at }}</div>
          </div>
        </div>

        <div class="pagination" v-if="total > pageSize">
          <el-pagination
            v-model:current-page="page"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next"
            @current-change="fetchList"
          />
        </div>
      </template>
      <el-empty v-else description="暂无通知">
        <el-button type="primary" @click="$router.push('/dashboard')">返回工作台</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
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

const items = ref<Notification[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

async function fetchList(): Promise<void> {
  loading.value = true
  try {
    const res = await notificationApi.list(page.value, pageSize.value)
    items.value = (res.data.items || []) as Notification[]
    total.value = (res.data.total || 0) as number
  } catch { /* ignore */ }
  finally { loading.value = false }
}

async function handleClick(n: Notification): Promise<void> {
  if (!n.is_read) {
    try {
      await notificationApi.markRead(n.id)
      n.is_read = true
    } catch { /* ignore */ }
  }
  if (n.related_id) {
    router.push(`/contracts/${n.related_id}`)
  }
}

async function handleMarkAllRead(): Promise<void> {
  try {
    await notificationApi.markAllRead()
    items.value.forEach(n => n.is_read = true)
  } catch { /* ignore */ }
}

onMounted(fetchList)
</script>

<style scoped>
.notification-page {
  max-width: 800px;
  margin: 0 auto;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-6);
}
.page-header h2 {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
}

.notif-card {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-4);
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-2);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 1px solid var(--color-border-light);
}
.notif-card:hover { box-shadow: var(--shadow-sm); }
.notif-card.unread {
  background: var(--color-primary-bg);
  border-color: var(--color-primary-light);
}
.notif-indicator {
  width: 10px; height: 10px; border-radius: 50%; margin-top: 4px; flex-shrink: 0;
}
.notif-indicator.unread { background: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-light); }
.notif-indicator.read { background: transparent; }
.notif-info { flex: 1; min-width: 0; }
.notif-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  display: flex; align-items: center; gap: var(--space-2);
}
.notif-content {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-top: var(--space-1);
}
.notif-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-top: var(--space-2);
}
.pagination { margin-top: var(--space-4); display: flex; justify-content: center; }
</style>
