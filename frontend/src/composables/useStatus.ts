// Shared status/type tag helpers used across views

type TagType = '' | 'success' | 'warning' | 'info' | 'danger'

const STATUS_TAG_MAP: Record<string, TagType> = {
  draft: 'info',
  pending_approval: 'warning',
  approved: 'success',
  archived: '',
  voided: 'danger',
}

const STATUS_TEXT_MAP: Record<string, string> = {
  draft: '草稿',
  pending_approval: '审批中',
  approved: '已通过',
  archived: '已归档',
  voided: '已作废',
}

const TYPE_TEXT_MAP: Record<string, string> = {
  purchase: '采购',
  sales: '销售',
  service: '服务',
  lease: '租赁',
  other: '其他',
}

export function statusTag(s: string): TagType {
  return STATUS_TAG_MAP[s] || 'info'
}

export function statusText(s: string): string {
  return STATUS_TEXT_MAP[s] || s
}

export function typeText(t: string): string {
  return TYPE_TEXT_MAP[t] || t
}
