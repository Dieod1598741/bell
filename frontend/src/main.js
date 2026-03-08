import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import ko from 'element-plus/dist/locale/ko.mjs'

import App from './App.vue'
import router from './router'
import { useUserStore } from '@/stores/userStore'
import './style.css'
import { sseClient } from '@/services/sseClient'

// SSE 연결 시작
sseClient.connect()

const app = createApp(App)
const pinia = createPinia()

// Element Plus 아이콘 등록
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(pinia)
app.use(router)
app.use(ElementPlus, { locale: ko })

// 프론트엔드 로그를 백엔드로 전달 (webview 환경에서만)
if (window.pywebview && window.pywebview.api && window.pywebview.api.log) {
  const originalLog = console.log
  const originalError = console.error
  const originalWarn = console.warn
  const originalInfo = console.info

  console.log = function (...args) {
    originalLog.apply(console, args)
    try {
      window.pywebview.api.log('log', args.join(' '))
    } catch (e) {
      // webview API 호출 실패 시 무시
    }
  }

  console.error = function (...args) {
    originalError.apply(console, args)
    try {
      window.pywebview.api.log('error', args.join(' '))
    } catch (e) {
      // webview API 호출 실패 시 무시
    }
  }

  console.warn = function (...args) {
    originalWarn.apply(console, args)
    try {
      window.pywebview.api.log('warn', args.join(' '))
    } catch (e) {
      // webview API 호출 실패 시 무시
    }
  }

  console.info = function (...args) {
    originalInfo.apply(console, args)
    try {
      window.pywebview.api.log('info', args.join(' '))
    } catch (e) {
      // webview API 호출 실패 시 무시
    }
  }

  console.log('[Frontend] 로그 전달 활성화됨')
}

// 초기 로드 시 사용자 정보 복원
const userStore = useUserStore()
userStore.loadUser()

app.mount('#app')

