import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/LoginView.vue'
import MainView from '@/views/MainView.vue'
import ChatView from '@/views/ChatView.vue'
import InboxView from '@/views/InboxView.vue'
import UserSelectView from '@/views/UserSelectView.vue'
import UserProfileView from '@/views/UserProfileView.vue'
import AdminView from '@/views/AdminView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: () => {
        const savedUser = localStorage.getItem('bell_user')
        return savedUser ? '/main' : '/login'
      }
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/main',
      name: 'main',
      component: MainView,
      meta: { requiresAuth: true }
    },
    {
      path: '/chat/:userId',
      name: 'chat',
      component: ChatView,
      props: true,
      meta: { requiresAuth: true }
    },
    {
      path: '/inbox',
      name: 'inbox',
      component: InboxView,
      meta: { requiresAuth: true }
    },
    {
      path: '/users',
      name: 'users',
      component: UserSelectView,
      meta: { requiresAuth: true }
    },
    {
      path: '/user/:userId',
      name: 'user-profile',
      component: UserProfileView,
      props: true,
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      name: 'admin',
      component: AdminView,
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/login'
    }
  ]
})

// 네비게이션 가드
router.beforeEach(async (to, from, next) => {
  // userStore에서 로그인 상태 확인 (localStorage 대신)
  const { useUserStore } = await import('@/stores/userStore')
  const userStore = useUserStore()
  const isLoggedIn = userStore.isLoggedIn
  const user = userStore.user

  console.log('[Router] 네비게이션 가드:', to.path, 'isLoggedIn:', isLoggedIn, 'user:', user?.id)

  // 로그인 필요 페이지인 경우
  if (to.meta.requiresAuth && !isLoggedIn) {
    console.log('[Router] 로그인 필요 - /login으로 리다이렉트')
    next('/login')
  } else if (to.path === '/login' && isLoggedIn) {
    // 이미 로그인된 경우 메인으로
    console.log('[Router] 이미 로그인됨 - /main으로 리다이렉트')
    next('/main')
  } else if (to.meta.requiresAdmin && (!user || user.permission?.toLowerCase() !== 'admin')) {
    // 관리자 권한 필요 페이지인 경우
    console.log('[Router] 관리자 권한 필요 - /main으로 리다이렉트')
    next('/main')
  } else {
    console.log('[Router] 네비게이션 허용:', to.path)
    next()
  }
})

export default router

