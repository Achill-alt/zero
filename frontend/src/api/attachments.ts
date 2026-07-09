import api from './index'

export const attachmentApi = {
  list: (contractId: number | string) => api.get(`/contracts/${contractId}/attachments`),
  upload: (contractId: number | string, formData: FormData) =>
    api.post(`/contracts/${contractId}/attachments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  downloadUrl: (id: number | string): string => {
    const base: string = api.defaults.baseURL || '/api/v1'
    return `${base}/attachments/${id}/download`
  },
  delete: (id: number | string) => api.delete(`/attachments/${id}`),
}
