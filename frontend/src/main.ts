import { createApp, type Component } from 'vue'
import { createPinia } from 'pinia'
import 'element-plus/dist/index.css'
import './styles/tokens.css'
import App from './App.vue'
import router from './router'
import { setupElementPlus } from './element-plus'

// Tree-shake: only import 18 icons actually used (was 2000+ via import *)
import {
  Plus, Edit, Checked, Clock, ArrowDown,
  SwitchButton, HomeFilled, Document, Search,
  Bell, Files, User, Setting, List, Collection,
  CircleCheck, Warning, Loading,
} from '@element-plus/icons-vue'

const app = createApp(App)

app.config.errorHandler = (err: unknown, _instance: Component | null, info: string) => {
  console.error('[Vue Error]', err, info)
}

window.addEventListener('unhandledrejection', (event: PromiseRejectionEvent) => {
  console.error('[Unhandled Promise]', event.reason)
})

app.use(createPinia())
app.use(router)
setupElementPlus(app)

// Register used icons globally (keeps Dashboard.vue dynamic <component :is> working)
const icons: Record<string, Component> = {
  Plus, Edit, Checked, Clock, ArrowDown,
  SwitchButton, HomeFilled, Document, Search,
  Bell, Files, User, Setting, List, Collection,
  CircleCheck, Warning, Loading,
}
for (const [key, component] of Object.entries(icons)) {
  app.component(key, component)
}

app.mount('#app')
