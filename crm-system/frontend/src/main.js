import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import { setApiRouter } from './api/index'
import { setStoreRouter } from './store/auth'

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
// 注入 router 到 api 和 store 模块，避免循环依赖导致 router undefined
setApiRouter(router)
setStoreRouter(router)
app.use(ElementPlus, { locale: undefined })
app.mount('#app')
