import api from './index'

export interface ContractApi {
  list(params?: Record<string, unknown>): Promise<any>
  create(data: Record<string, unknown>): Promise<any>
  get(id: number | string): Promise<any>
  update(id: number | string, data: Record<string, unknown>): Promise<any>
  submit(id: number | string): Promise<any>
  archive(id: number | string): Promise<any>
  void(id: number | string): Promise<any>
  expiring(params?: Record<string, unknown>): Promise<any>
  templates(params?: Record<string, unknown>): Promise<any>
}

export const contractApi = {
  list: (params?: Record<string, unknown>) => api.get('/contracts', { params }),
  create: (data: Record<string, unknown>) => api.post('/contracts', data),
  get: (id: number | string) => api.get(`/contracts/${id}`),
  update: (id: number | string, data: Record<string, unknown>) => api.put(`/contracts/${id}`, data),
  submit: (id: number | string) => api.post(`/contracts/${id}/submit`),
  archive: (id: number | string) => api.post(`/contracts/${id}/archive`),
  void: (id: number | string) => api.post(`/contracts/${id}/void`),
  expiring: (params?: Record<string, unknown>) => api.get('/contracts/expiring/list', { params }),
  templates: (params?: Record<string, unknown>) => api.get('/contracts/templates/all', { params }),
}
