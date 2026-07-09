import api from './index'

export const searchApi = {
  search: (params: Record<string, unknown>) => api.get('/search', { params }),
}
