# FEAT-203 TipTap 富文本编辑器

> **完成日期：** 2026-07-09  
> **版本：** v1.2  
> **状态：** ✅ 已完成

## 1. 背景

合同内容的纯文本 `<textarea>` 无法支持格式化（加粗、斜体、标题、列表等），合同正文排版受限。需要集成富文本编辑器提升合同撰写体验。

## 2. 方案选择

| 方案 | 优势 | 劣势 |
|------|------|------|
| **TipTap v3** (ProseMirror) | Vue 3 一等公民、TypeScript 原生、模块化、活跃维护 | 包体积较大 (~400KB gzip 126KB) |
| Quill | 轻量、API 简单 | Vue 3 集成较弱、生态不如 TipTap |

**最终选择：TipTap v3**

## 3. 实现方案

### 3.1 架构

```
RichTextEditor.vue (可复用组件)
  ├── TipTap useEditor() + StarterKit + Placeholder
  ├── Toolbar: Bold / Italic / H2 / H3 / BulletList / OrderedList / Blockquote / Undo / Redo
  ├── v-model 双向绑定 HTML 字符串
  └── Element Plus 视觉对齐（聚焦边框高亮、禁用态）

useSanitize.ts (DOMPurify 封装)
  └── sanitizeHtml() — 白名单标签 + 属性过滤

ContractCreate.vue → <RichTextEditor v-model="form.content" />
ContractEdit.vue   → <RichTextEditor v-model="form.content" />
ContractDetail.vue → <div v-html="sanitizedContent" />
```

### 3.2 依赖

```json
{
  "@tiptap/vue-3": "^3.x",
  "@tiptap/pm": "^3.x",
  "@tiptap/starter-kit": "^3.x",
  "@tiptap/extension-placeholder": "^3.x",
  "@floating-ui/dom": "^1.6.0",
  "dompurify": "^3.x"
}
```

### 3.3 编辑器配置

- **启用扩展：** bold, italic, heading (H2/H3), bulletList, orderedList, listItem, blockquote, code, hardBreak, history, placeholder
- **禁用扩展：** codeBlock, horizontalRule, strike（合同场景不需要）
- **输出格式：** HTML 字符串（与后端 `content` Text 字段兼容）
- **空内容处理：** TipTap 空编辑器输出 `<p></p>` → 组件自动转为空字符串

### 3.4 HTML 消毒

使用 DOMPurify 对 `v-html` 渲染的内容进行消毒，防止 XSS：

```typescript
ALLOWED_TAGS: ['p','br','strong','em','u','s','h1'-'h6','ul','ol','li','blockquote','code','pre','a','span','div']
ALLOWED_ATTR: ['href','target','class']
```

## 4. 涉及文件

| 文件 | 变更 | 说明 |
|------|------|------|
| `frontend/src/components/RichTextEditor.vue` | 新建 | TipTap 封装组件 (~250 行) |
| `frontend/src/composables/useSanitize.ts` | 新建 | DOMPurify 消毒工具 |
| `frontend/src/views/ContractCreate.vue` | 修改 | textarea → RichTextEditor + @blur 表单验证 |
| `frontend/src/views/ContractEdit.vue` | 修改 | textarea → RichTextEditor |
| `frontend/src/views/ContractDetail.vue` | 修改 | v-html + sanitizeHtml + 空内容检测 |
| `frontend/package.json` | 修改 | 新增 6 个 npm 依赖 |

## 5. 兼容性

| 场景 | 行为 |
|------|------|
| 已有纯文本合同 | Detail 页正常显示（v-html 对纯文本无副作用） |
| 新建富文本合同 | HTML 内容存入 DB，Detail 页格式化渲染 |
| 编辑已有合同 | 编辑器回显 HTML 内容（watch modelValue → setContent） |
| 模板应用 | `applyTemplate()` 设置 `form.content` → watch 触发 setContent |
| 空内容 | 显示 `(无内容)` 占位 |

## 6. 验证

```bash
vue-tsc --noEmit    # 0 错误
vite build           # 5.47s 通过
pytest tests/ -v     # 44/44 通过（无回归）
```

