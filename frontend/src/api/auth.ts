import api from './index'

export interface AuthApi {
  login(username: string, password: string): Promise<any>
  register(data: Record<string, unknown>): Promise<any>
  me(): Promise<any>
}

export const authApi = {
  login: (username: string, password: string) => api.post('/auth/login', { username, password }),
  register: (data: Record<string, unknown>) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
}
