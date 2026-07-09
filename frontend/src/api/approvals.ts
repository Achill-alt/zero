import api from './index'

export const approvalApi = {
  pending: () => api.get('/approvals/pending'),
  approve: (id: number | string, comment?: string) => api.post(`/approvals/${id}/approve`, { comment }),
  reject: (id: number | string, comment?: string) => api.post(`/approvals/${id}/reject`, { comment }),
  withdraw: (id: number | string) => api.post(`/approvals/${id}/withdraw`),
  chainList: () => api.get('/approval-chains'),
  chainCreate: (data: Record<string, unknown>) => api.post('/approval-chains', data),
  chainUpdate: (id: number | string, data: Record<string, unknown>) => api.put(`/approval-chains/${id}`, data),
  chainDelete: (id: number | string) => api.delete(`/approval-chains/${id}`),
}
