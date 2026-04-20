import { createApp } from 'vue'

import App from './App.vue'

import 'element-plus/dist/index.css' // 引入Element Plus的样式
import './styles/main.css'
import ElementPlus  from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import router from './router'
import {createPinia} from 'pinia'
const app = createApp(App)
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate) // 使用持久化插件
app.use(pinia)
// 全局注册Element Plus组件
app.use(ElementPlus)
app.use(router)

// 全局注册Element Plus图标组件
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 挂载应用实例（确保使用已经配置的app）
app.mount('#app')
