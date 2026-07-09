import api from './index'

export const notificationApi = {
  list: (page = 1, pageSize = 20) =>
    api.get('/notifications', { params: { page, page_size: pageSize } }),
  unreadCount: () =>
    api.get('/notifications/unread-count'),
  markRead: (id: number | string) =>
    api.put(`/notifications/${id}/read`),
  markAllRead: () =>
    api.put('/notifications/read-all'),
}
