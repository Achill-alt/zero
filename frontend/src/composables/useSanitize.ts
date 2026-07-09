import DOMPurify from 'dompurify'

/**
 * Sanitize HTML string before rendering with v-html.
 * Uses DOMPurify to strip XSS vectors while preserving
 * formatting tags produced by TipTap (ProseMirror).
 */
export function sanitizeHtml(html: string): string {
  if (!html) return ''
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'em', 'u', 's',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li', 'blockquote', 'code', 'pre',
      'a', 'span', 'div',
    ],
    ALLOWED_ATTR: ['href', 'target', 'class'],
  })
}
