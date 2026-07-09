<template>
  <div class="search-page">
    <div class="page-header">
      <h2>全文检索</h2>
      <p class="page-desc">搜索合同标题与内容，支持中文分词</p>
    </div>

    <div class="search-bar">
      <el-input v-model="query" placeholder="输入关键词搜索合同标题和内容..." size="large" clearable
        @keyup.enter="doSearch" style="flex:1; max-width:520px">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button type="primary" size="large" :loading="loading" @click="doSearch">
        <el-icon><Search /></el-icon> 搜索
      </el-button>
    </div>

    <div class="filters">
      <el-select v-model="filterType" placeholder="合同类型" clearable size="small" style="width:120px">
        <el-option label="采购" value="purchase" /><el-option label="销售" value="sales" />
        <el-option label="服务" value="service" /><el-option label="租赁" value="lease" /><el-option label="其他" value="other" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="合同状态" clearable size="small" style="width:120px">
        <el-option label="草稿" value="draft" /><el-option label="审批中" value="pending_approval" />
        <el-option label="已通过" value="approved" /><el-option label="已归档" value="archived" /><el-option label="已作废" value="voided" />
      </el-select>
      <el-button size="small" @click="filterType='';filterStatus='';doSearch()" :disabled="!filterType && !filterStatus">清除筛选</el-button>
    </div>

    <div v-if="searched" class="search-summary">
      共找到 <strong>{{ total }}</strong> 条结果
    </div>

    <div v-if="items.length > 0" class="results" v-loading="loading">
      <el-card v-for="item in items" :key="item.id" shadow="hover" class="result-card" @click="$router.push(`/contracts/${item.id}`)">
        <h3 v-if="item.title_highlight" v-html="item.title_highlight" />
        <h3 v-else>{{ item.title }}</h3>
        <div class="meta">
          <el-tag size="small" :type="statusTag(item.status)">{{ statusText(item.status) }}</el-tag>
          <el-tag size="small" type="info">{{ typeText(item.contract_type) }}</el-tag>
          <span v-if="item.amount" class="meta-amount">¥{{ item.amount.toLocaleString() }}</span>
          <span class="meta-date">{{ item.start_date }} ~ {{ item.end_date }}</span>
        </div>
        <p v-if="item.content_highlight" class="snippet" v-html="item.content_highlight" />
        <p v-else class="snippet">{{ (item.content || '').slice(0, 200) }}</p>
      </el-card>
    </div>

    <el-empty v-if="searched && items.length === 0 && !loading" description="未找到匹配结果" />

    <div v-if="total > pageSize" style="display:flex;justify-content:center;margin-top:var(--space-4)">
      <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total"
        layout="total, prev, pager, next" @current-change="doSearch" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { searchApi } from '../api/search'
import { statusTag, statusText, typeText } from '../composables/useStatus'

interface SearchResultItem {
  id: number
  title: string
  title_highlight?: string
  content?: string
  content_highlight?: string
  status: string
  contract_type: string
  amount: number | null
  start_date: string
  end_date: string
}

const query = ref('')
const items = ref<SearchResultItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const searched = ref(false)
const filterType = ref('')
const filterStatus = ref('')

async function doSearch(): Promise<void> {
  if (!query.value.trim() && !filterType.value && !filterStatus.value) return
  loading.value = true
  searched.value = true
  try {
    const params: Record<string, unknown> = { q: query.value.trim(), page: page.value, page_size: pageSize.value }
    if (filterType.value) params.type = filterType.value
    if (filterStatus.value) params.status = filterStatus.value
    const res = await searchApi.search(params)
    items.value = (res.data.items || []) as SearchResultItem[]
    total.value = (res.data.total || 0) as number
  } finally { loading.value = false }
}
</script>

<style scoped>
.page-header { margin-bottom: var(--space-6); }
.page-header h2 { font-size: var(--font-size-2xl); font-weight: var(--font-weight-bold); color: var(--color-text); }
.page-desc { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-top: var(--space-1); }

.search-bar { display: flex; gap: var(--space-3); align-items: center; }
.filters { margin-top: var(--space-3); display: flex; gap: var(--space-3); align-items: center; }

.search-summary {
  margin-top: var(--space-4);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
.search-summary strong { color: var(--color-primary); font-weight: var(--font-weight-semibold); }

.results { margin-top: var(--space-3); }
.result-card {
  margin-top: var(--space-3);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.result-card:hover {
  border-color: var(--color-primary) !important;
  box-shadow: var(--shadow-md) !important;
}
.result-card h3 {
  margin: 0 0 var(--space-2) 0;
  font-size: var(--font-size-md);
}
.result-card h3 :deep(mark) {
  background: #fef3c7;
  color: var(--color-text);
  padding: 0 2px;
  border-radius: 2px;
}
.result-card .meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}
.meta-amount { font-size: var(--font-size-sm); color: var(--color-text-secondary); }
.meta-date { font-size: var(--font-size-sm); color: var(--color-text-tertiary); }
.result-card .snippet {
  color: var(--color-text-secondary);
  font-size: var(--font-size-base);
  margin: 0;
  line-height: var(--line-height-relaxed);
}
.result-card .snippet :deep(mark) {
  background: #fef3c7;
  color: var(--color-text);
  padding: 0 2px;
  border-radius: 2px;
}
</style>
