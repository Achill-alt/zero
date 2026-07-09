/**
 * On-demand Element Plus component registration.
 * Only imports the 31 components actually used across the app,
 * instead of ~200 via `app.use(ElementPlus)`.
 *
 * This cuts dev-mode cold start from ~8s to ~2s by reducing
 * the number of modules Vite must transform on first load.
 */
import type { App, Component } from 'vue'

import {
  // layout
  ElRow, ElCol,
  // basic
  ElButton, ElBadge, ElTag, ElIcon,
  // form
  ElForm, ElFormItem, ElInput, ElInputNumber, ElSelect, ElOption,
  ElDatePicker, ElSwitch, ElUpload,
  // data
  ElTable, ElTableColumn, ElPagination, ElDescriptions, ElDescriptionsItem,
  // navigation
  ElMenu, ElMenuItem, ElDropdown, ElDropdownMenu, ElDropdownItem,
  // feedback
  ElDialog, ElPopover, ElEmpty,
  // display
  ElCard, ElTimeline, ElTimelineItem,
  // config (locale)
  ElConfigProvider,
} from 'element-plus'

/** All components used as `<el-xxx>` tags in templates */
const components: [string, Component][] = [
  ['ElRow', ElRow],
  ['ElCol', ElCol],
  ['ElButton', ElButton],
  ['ElBadge', ElBadge],
  ['ElTag', ElTag],
  ['ElIcon', ElIcon],
  ['ElForm', ElForm],
  ['ElFormItem', ElFormItem],
  ['ElInput', ElInput],
  ['ElInputNumber', ElInputNumber],
  ['ElSelect', ElSelect],
  ['ElOption', ElOption],
  ['ElDatePicker', ElDatePicker],
  ['ElSwitch', ElSwitch],
  ['ElUpload', ElUpload],
  ['ElTable', ElTable],
  ['ElTableColumn', ElTableColumn],
  ['ElPagination', ElPagination],
  ['ElDescriptions', ElDescriptions],
  ['ElDescriptionsItem', ElDescriptionsItem],
  ['ElMenu', ElMenu],
  ['ElMenuItem', ElMenuItem],
  ['ElDropdown', ElDropdown],
  ['ElDropdownMenu', ElDropdownMenu],
  ['ElDropdownItem', ElDropdownItem],
  ['ElDialog', ElDialog],
  ['ElPopover', ElPopover],
  ['ElEmpty', ElEmpty],
  ['ElCard', ElCard],
  ['ElTimeline', ElTimeline],
  ['ElTimelineItem', ElTimelineItem],
  ['ElConfigProvider', ElConfigProvider],
]

export function setupElementPlus(app: App): void {
  for (const [name, comp] of components) {
    app.component(name, comp)
  }
}
