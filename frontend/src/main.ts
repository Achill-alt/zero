import { createApp, type Component } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import './styles/tokens.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.config.errorHandler = (err: unknown, _instance: Component | null, info: string) => {
  console.error('[Vue Error]', err, info)
}

window.addEventListener('unhandledrejection', (event: PromiseRejectionEvent) => {
  console.error('[Unhandled Promise]', event.reason)
})

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

// Register all icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component as Component)
}

app.mount('#app')
