import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
})

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => {
    // For binary responses (blob/arraybuffer), return the full response
    // so callers can access response.data (the Blob)
    if (response.config.responseType === 'blob' || response.config.responseType === 'arraybuffer') {
      return response
    }
    return response.data
  },
  (error) => {
    const status: number | undefined = error.response?.status
    const detail = error.response?.data?.detail
    let msg: string

    // FastAPI 422 validation error: detail is array of {loc, msg, type}
    if (Array.isArray(detail)) {
      msg = detail.map((e: { loc: string[]; msg: string }) => {
        const field = e.loc?.slice(-1)[0] || ''
        return field ? `${field}: ${e.msg}` : e.msg
      }).join('；')
    } else {
      msg = (detail as string) || error.message || '请求失败'
    }

    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }

    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default api
