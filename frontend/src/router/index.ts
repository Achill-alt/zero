import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useProgressBar } from '../composables/useProgressBar'

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { public: true } },
  { path: '/dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/contracts', name: 'ContractList', component: () => import('../views/ContractList.vue') },
  { path: '/contracts/create', name: 'ContractCreate', component: () => import('../views/ContractCreate.vue') },
  { path: '/contracts/:id', name: 'ContractDetail', component: () => import('../views/ContractDetail.vue') },
  { path: '/contracts/:id/edit', name: 'ContractEdit', component: () => import('../views/ContractEdit.vue') },
  { path: '/approvals', name: 'ApprovalCenter', component: () => import('../views/ApprovalCenter.vue') },
  { path: '/templates', name: 'TemplateManage', component: () => import('../views/TemplateManage.vue') },
  { path: '/expiring', name: 'ExpiringPanel', component: () => import('../views/ExpiringPanel.vue') },
  { path: '/admin/users', name: 'UserManage', component: () => import('../views/UserManage.vue') },
  { path: '/admin/approval-chains', name: 'ApprovalChainConfig', component: () => import('../views/ApprovalChainConfig.vue') },
  { path: '/admin/audit-logs', name: 'AuditLogs', component: () => import('../views/AuditLogs.vue') },
  { path: '/admin/register', name: 'Register', component: () => import('../views/Register.vue') },
  { path: '/search', name: 'Search', component: () => import('../views/Search.vue') },
  { path: '/notifications', name: 'NotificationList', component: () => import('../views/NotificationList.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  if (to.meta.public) {
    next()
  } else if (!authStore.token) {
    next('/login')
  } else {
    next()
  }
})

// Progress bar
const { start, done } = useProgressBar()
router.beforeEach((_to, from, next) => {
  if (from.name) start()
  next()
})
router.afterEach(() => done())
router.onError(() => done())

export default router
