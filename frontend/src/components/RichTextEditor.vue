<template>
  <div class="rich-text-editor" :class="{ 'is-disabled': disabled }">
    <!-- Toolbar -->
    <div v-if="editor && !disabled" class="editor-toolbar">
      <el-button
        size="small"
        :type="editor.isActive('bold') ? 'primary' : 'default'"
        @click="editor.chain().focus().toggleBold().run()"
        title="加粗 (Ctrl+B)"
      >
        <strong>B</strong>
      </el-button>
      <el-button
        size="small"
        :type="editor.isActive('italic') ? 'primary' : 'default'"
        @click="editor.chain().focus().toggleItalic().run()"
        title="斜体 (Ctrl+I)"
      >
        <em>I</em>
      </el-button>
      <el-button
        size="small"
        :type="editor.isActive('heading', { level: 2 }) ? 'primary' : 'default'"
        @click="editor.chain().focus().toggleHeading({ level: 2 }).run()"
        title="标题2"
      >
        H2
      </el-button>
      <el-button
        size="small"
        :type="editor.isActive('heading', { level: 3 }) ? 'primary' : 'default'"
        @click="editor.chain().focus().toggleHeading({ level: 3 }).run()"
        title="标题3"
      >
        H3
      </el-button>
      <span class="toolbar-divider" />
      <el-button
        size="small"
        :type="editor.isActive('bulletList') ? 'primary' : 'default'"
        @click="editor.chain().focus().toggleBulletList().run()"
        title="无序列表"
      >
        • 列表
      </el-button>
      <el-button
        size="small"
        :type="editor.isActive('orderedList') ? 'primary' : 'default'"
        @click="editor.chain().focus().toggleOrderedList().run()"
        title="有序列表"
      >
        1. 列表
      </el-button>
      <el-button
        size="small"
        :type="editor.isActive('blockquote') ? 'primary' : 'default'"
        @click="editor.chain().focus().toggleBlockquote().run()"
        title="引用"
      >
        " 引用
      </el-button>
      <span class="toolbar-divider" />
      <el-button
        size="small"
        :disabled="!editor.can().undo()"
        @click="editor.chain().focus().undo().run()"
        title="撤销 (Ctrl+Z)"
      >
        ↶
      </el-button>
      <el-button
        size="small"
        :disabled="!editor.can().redo()"
        @click="editor.chain().focus().redo().run()"
        title="重做 (Ctrl+Y)"
      >
        ↷
      </el-button>
    </div>

    <!-- Editor content area -->
    <EditorContent :editor="editor" class="editor-content" @blur="handleBlur" />
  </div>
</template>

<script setup lang="ts">
import { watch, onBeforeUnmount } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'

interface Props {
  modelValue: string
  disabled?: boolean
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  disabled: false,
  placeholder: '请输入合同内容...',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'blur'): void
}>()

const editor = useEditor({
  content: props.modelValue,
  editable: !props.disabled,
  extensions: [
    StarterKit.configure({
      codeBlock: false,
      horizontalRule: false,
      strike: false,
    }),
    Placeholder.configure({
      placeholder: props.placeholder,
    }),
  ],
  editorProps: {
    attributes: {
      class: 'prose-mirror-editor',
    },
  },
  onUpdate: ({ editor: ed }) => {
    // TipTap always has at least <p></p> even when empty
    const html = ed.getHTML()
    emit('update:modelValue', html === '<p></p>' ? '' : html)
  },
  onBlur: () => {
    emit('blur')
  },
})

function handleBlur(): void {
  emit('blur')
}

// Watch for external modelValue changes (e.g. template application)
watch(
  () => props.modelValue,
  (val) => {
    if (editor.value) {
      const currentHTML = editor.value.getHTML()
      const currentClean = currentHTML === '<p></p>' ? '' : currentHTML
      if (val !== currentClean) {
        editor.value.commands.setContent(val || '', { emitUpdate: false })
      }
    }
  },
)

// Watch disabled prop
watch(
  () => props.disabled,
  (val) => {
    editor.value?.setEditable(!val)
  },
)

// Cleanup on unmount
onBeforeUnmount(() => {
  editor.value?.destroy()
})
</script>

<style scoped>
.rich-text-editor {
  border: 1px solid var(--el-border-color, #dcdfe6);
  border-radius: var(--el-border-radius-base, 4px);
  transition: border-color 0.2s;
  background: var(--el-bg-color, #fff);
}

.rich-text-editor:focus-within {
  border-color: var(--el-color-primary, #409eff);
}

.rich-text-editor.is-disabled {
  background: var(--el-disabled-bg-color, #f5f7fa);
  cursor: not-allowed;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 1px;
  padding: 6px 8px;
  border-bottom: 1px solid var(--el-border-color-light, #e4e7ed);
  background: var(--el-bg-color-page, #fafafa);
  border-radius: 3px 3px 0 0;
  flex-wrap: wrap;
}

.editor-toolbar .el-button {
  min-width: 28px;
  height: 28px;
  padding: 0 6px;
  font-size: 12px;
}

.toolbar-divider {
  display: inline-block;
  width: 1px;
  height: 20px;
  background: var(--el-border-color, #dcdfe6);
  margin: 0 4px;
}

.editor-content {
  padding: 8px 12px;
  min-height: 200px;
  max-height: 500px;
  overflow-y: auto;
}

/* ProseMirror editor styles */
.editor-content :deep(.ProseMirror) {
  outline: none;
  min-height: 180px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--el-text-color-regular, #606266);
  word-break: break-word;
}

.editor-content :deep(.ProseMirror p) {
  margin: 0 0 0.5em 0;
}

.editor-content :deep(.ProseMirror p:last-child) {
  margin-bottom: 0;
}

.editor-content :deep(.ProseMirror h2) {
  font-size: 18px;
  font-weight: 600;
  margin: 0.8em 0 0.4em 0;
  line-height: 1.4;
}

.editor-content :deep(.ProseMirror h3) {
  font-size: 16px;
  font-weight: 600;
  margin: 0.6em 0 0.3em 0;
  line-height: 1.4;
}

.editor-content :deep(.ProseMirror ul),
.editor-content :deep(.ProseMirror ol) {
  padding-left: 1.5em;
  margin: 0.4em 0;
}

.editor-content :deep(.ProseMirror li) {
  margin: 0.2em 0;
}

.editor-content :deep(.ProseMirror blockquote) {
  border-left: 3px solid var(--el-color-primary, #409eff);
  padding-left: 1em;
  margin: 0.5em 0;
  color: var(--el-text-color-secondary, #909399);
}

.editor-content :deep(.ProseMirror code) {
  background: var(--el-bg-color-page, #f5f7fa);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
}

.editor-content :deep(.ProseMirror pre) {
  background: var(--el-bg-color-page, #f5f7fa);
  padding: 10px 14px;
  border-radius: 4px;
  font-size: 13px;
  overflow-x: auto;
}

.editor-content :deep(.ProseMirror pre code) {
  background: transparent;
  padding: 0;
}

/* Placeholder styling */
.editor-content :deep(.ProseMirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  color: var(--el-text-color-placeholder, #c0c4cc);
  pointer-events: none;
  height: 0;
}

/* Disabled state */
.is-disabled .editor-content :deep(.ProseMirror) {
  color: var(--el-text-color-placeholder, #c0c4cc);
}
</style>
