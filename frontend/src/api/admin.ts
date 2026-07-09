import api from './index'

export const adminApi = {
  users: (params?: Record<string, unknown>) => api.get('/users', { params }),
  updateUser: (id: number | string, data: Record<string, unknown>) => api.put(`/users/${id}`, data),
  templates: (data: Record<string, unknown>) => api.post('/templates', data),
  updateTemplate: (id: number | string, data: Record<string, unknown>) => api.put(`/templates/${id}`, data),
  deleteTemplate: (id: number | string) => api.delete(`/templates/${id}`),
  auditLogs: (params?: Record<string, unknown>) => api.get('/audit-logs', { params }),
}
