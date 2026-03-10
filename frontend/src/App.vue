<template>
  <!-- 초기 로딩 화면 -->
  <div v-if="isInitializing" class="loading-screen">
    <div class="loading-content">
      <h1 class="loading-text">bell</h1>
    </div>
  </div>
  <!-- 메인 앱 -->
  <router-view v-else />
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import { restoreSession } from '@/composables/useSession'
import { getUser } from '@/services/userService'
import { sseClient } from '@/services/sseClient'
import { ElNotification } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const isInitializing = ref(true)

onMounted(async () => {
  // 자동 로그인 체크를 먼저 수행 (로그인 화면이 보이지 않도록)
  await checkAutoLogin()
  
  // 세션 복원
  await restoreSession()
  
  // 활동 상태 모니터링 시작 (마우스 움직임 기반 자리비움 감지)
  startActivityMonitoring()

  // SSE 알림 리스너 등록
  setupNotificationListeners()
  
  // 초기화 완료
  isInitializing.value = false
})

// 자동 로그인 체크
const checkAutoLogin = async () => {
  // 이미 로그인된 상태면 메인으로 이동
  if (userStore.isLoggedIn && userStore.user) {
    if (router.currentRoute.value.path !== '/main') {
      router.replace('/main')
    }
    return
  }
  
  // API 준비 대기
  let retryCount = 0
  const maxRetries = 20
  while (!window.pywebview?.api?.getLoginSettings && retryCount < maxRetries) {
    await new Promise(resolve => setTimeout(resolve, 50))
    retryCount++
  }
  
  // 로그인 설정 조회
  if (window.pywebview?.api?.getLoginSettings) {
    try {
      const settingsResult = await window.pywebview.api.getLoginSettings()
      if (settingsResult.success && settingsResult.data) {
        const settings = settingsResult.data
        
        // 자동 로그인이 체크되어 있고 아이디가 저장되어 있으면
        if (settings.auto_login && settings.saved_user_id) {
          const userId = settings.saved_user_id
          
          // 백엔드에서 저장된 사용자 정보 확인
          if (window.pywebview?.api?.getUserInfo) {
            const userResult = await window.pywebview.api.getUserInfo()
            if (userResult?.success && userResult?.data) {
              const userData = userResult.data
              if (userData.id === userId) {
                // 저장된 사용자 정보가 있으면 자동 로그인
                await userStore.setUser(userData)
                const { updateUserStatus } = await import('@/services/statusService')
                await updateUserStatus(userId, 'online')
                if (router.currentRoute.value.path !== '/main') {
                  router.replace('/main')
                }
                return
              }
            }
          }
        }
      }
    } catch (e) {
      console.error('[App] 자동 로그인 체크 실패:', e)
    }
  }
}

// 로그인 상태 및 사용자 ID 변경 감지
let currentMonitoringUserId = null
watch(
  () => userStore.isLoggedIn && userStore.user?.id,
  async (userId) => {
    if (userId) {
      // 사용자 ID가 변경되었으면 이전 모니터링 중지
      if (currentMonitoringUserId && currentMonitoringUserId !== userId) {
        stopActivityMonitoring()
        currentMonitoringUserId = null
      }
      
      // 새 사용자로 로그인한 경우에만 모니터링 시작
      if (!currentMonitoringUserId) {
        await new Promise(resolve => setTimeout(resolve, 300))
        await restoreSession()
        // 활동 모니터링 시작
        currentMonitoringUserId = userId
        startActivityMonitoring()
      }
    } else {
      // 로그아웃 시 활동 모니터링 중지
      stopActivityMonitoring()
      currentMonitoringUserId = null
    }
  }
)

// 활동 상태 모니터링 (마우스 움직임 기반)
let activityCheckInterval = null
const startActivityMonitoring = () => {
  // 로그인 상태가 아니면 모니터링 시작하지 않음
  if (!userStore.isLoggedIn || !userStore.user) {
    return
  }
  
  const monitoringUserId = userStore.user.id
  console.log(`[App] 활동 모니터링 시작: user_id=${monitoringUserId}`)
  
  // 기존 인터벌 정리
  if (activityCheckInterval) {
    clearInterval(activityCheckInterval)
    activityCheckInterval = null
  }
  
  // 1분마다 활동 상태 확인
  activityCheckInterval = setInterval(async () => {
    // 로그인 상태 및 사용자 ID 확인 (다른 사용자로 변경되었거나 로그아웃 시 중지)
    if (!userStore.isLoggedIn || !userStore.user || userStore.user.id !== monitoringUserId) {
      console.log(`[App] 활동 모니터링 중지: user_id 변경 또는 로그아웃`)
      stopActivityMonitoring()
      return
    }
    
    if (window.pywebview?.api?.getActivityStatus) {
      try {
        const result = await window.pywebview.api.getActivityStatus()
        if (result.success && result.data) {
          const isActive = result.data.is_active
          const currentStatus = userStore.userStatus
          
          // 오프라인 상태일 때는 활동 모니터링 하지 않음
          if (currentStatus === 'offline') {
            return
          }
          
          // 활동 상태에 따라 상태 업데이트 (현재 로그인된 사용자에게만)
          if (isActive && currentStatus === 'away') {
            // 활동 재개 -> 온라인으로 복귀
            const { updateUserStatus } = await import('@/services/statusService')
            await updateUserStatus(monitoringUserId, 'online')
            userStore.setStatus('online')
            console.log(`[App] 활동 재개 - 온라인으로 복귀: user_id=${monitoringUserId}`)
          } else if (!isActive && currentStatus === 'online') {
            // 활동 없음 -> 자리비움으로 변경
            const { updateUserStatus } = await import('@/services/statusService')
            await updateUserStatus(monitoringUserId, 'away')
            userStore.setStatus('away')
            console.log(`[App] 활동 없음 - 자리비움으로 변경: user_id=${monitoringUserId}`)
          }
        }
      } catch (e) {
        console.error('[App] 활동 상태 확인 실패:', e)
      }
    }
  }, 60000) // 1분
}

const stopActivityMonitoring = () => {
  if (activityCheckInterval) {
    clearInterval(activityCheckInterval)
    activityCheckInterval = null
    console.log('[App] 활동 모니터링 중지됨')
  }
}

// SSE 알림 팝업 등록
const setupNotificationListeners = () => {
  // 새 채팅 메시지 알림
  sseClient.on('NEW_CHAT', (msg) => {
    const currentUserId = userStore.user?.id
    if (!currentUserId || msg.sender_user_id === currentUserId) return
    ElNotification({
      title: '💬 새 메시지',
      message: msg.content?.length > 40 ? msg.content.substring(0, 40) + '...' : msg.content,
      type: 'info',
      duration: 4000,
      position: 'bottom-right'
    })
  })

  // 새 쪽지 / 회의요청 알림
  sseClient.on('NEW_ANNOUNCEMENT', (data) => {
    const currentUserId = userStore.user?.id
    if (!currentUserId || data.sender_user_id === currentUserId) return
    const isMeeting = data.type === 'meeting'
    ElNotification({
      title: isMeeting ? '📅 회의 요청' : '✉️ 새 쪽지',
      message: data.message?.length > 40 ? data.message.substring(0, 40) + '...' : data.message,
      type: isMeeting ? 'warning' : 'success',
      duration: 5000,
      position: 'bottom-right'
    })
  })
}

// 컴포넌트 언마운트 시 정리
onUnmounted(() => {
  stopActivityMonitoring()
})
</script>

<style scoped>
.loading-screen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #ffffff;
  z-index: 9999;
}

.loading-content {
  text-align: center;
}

.loading-text {
  font-size: 48px;
  font-weight: 600;
  color: #3b82f6;
  letter-spacing: 2px;
  margin: 0;
}
</style>

