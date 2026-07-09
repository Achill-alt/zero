import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/auth'

interface User {
  id: number
  username: string
  role: 'admin' | 'approver' | 'handler'
  approver_role?: string | null
  department?: string
  display_name?: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<User | null>(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed<boolean>(() => !!token.value)
  const isAdmin = computed<boolean>(() => user.value?.role === 'admin')
  const isApprover = computed<boolean>(() => user.value?.role === 'approver')
  const isHandler = computed<boolean>(() => user.value?.role === 'handler')

  async function login(username: string, password: string) {
    const res = await authApi.login(username, password)
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem('token', token.value)
    localStorage.setItem('user', JSON.stringify(user.value))
    return res
  }

  function logout(): void {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  async function fetchMe() {
    const res = await authApi.me()
    user.value = res.data
    localStorage.setItem('user', JSON.stringify(user.value))
  }

  return { token, user, isLoggedIn, isAdmin, isApprover, isHandler, login, logout, fetchMe }
})
