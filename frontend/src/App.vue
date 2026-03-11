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
  // SSE 연결 먼저 시작 (DB_UPDATE, NEW_CHAT, NEW_ANNOUNCEMENT 수신을 위해)
  sseClient.connect()

  // 자동 로그인 체크를 먼저 수행 (로그인 화면이 보이지 않도록)
  await checkAutoLogin()

  // 활동 상태 모니터링 시작 (마우스 움직임 기반 자리비움 감지)
  startActivityMonitoring()

  // SSE 알림 리스너 등록
  setupNotificationListeners()

  // 초기화 완료
  isInitializing.value = false
})

// 자동 로그인 체크 - 백엔드 파일에 저장된 사용자 정보 기반으로 복원
const checkAutoLogin = async () => {
  // 이미 로그인된 상태면 메인으로 이동
  if (userStore.isLoggedIn && userStore.user) {
    if (router.currentRoute.value.path !== '/main') {
      router.replace('/main')
    }
    return
  }

  // API 준비 대기 (최대 6초 — Windows에서 브리지 준비 시간이 macOS보다 길 수 있음)
  let retryCount = 0
  const maxRetries = 60  // 40 → 60 (6초)
  while (!window.pywebview?.api?.getUserInfo && retryCount < maxRetries) {
    await new Promise(resolve => setTimeout(resolve, 100))
    retryCount++
  }

  if (!window.pywebview?.api?.getUserInfo) {
    console.log('[App] API 준비 안 됨 (6초 대기 초과), 로그인 페이지로 이동')
    // ※ 타임아웃 시 /login으로 명시 이동 (흰 화면 방지)
    if (router.currentRoute.value.path !== '/login') {
      router.replace('/login')
    }
    return
  }

  try {
    // 1. 백엔드에 저장된 사용자 정보 확인 (로그인 여부와 무관하게 복원)
    const userResult = await window.pywebview.api.getUserInfo()
    if (userResult?.success && userResult?.data?.id) {
      const userData = userResult.data
      console.log('[App] 저장된 사용자 정보 복원:', userData.id)
      await userStore.setUser(userData)

      // 상태를 online으로 복원 (트레이 포함)
      const { updateUserStatus } = await import('@/services/statusService')
      await updateUserStatus(userData.id, 'online')

      if (router.currentRoute.value.path !== '/main') {
        router.replace('/main')
      }
      return
    }

    // 2. 백엔드 사용자 정보 없음 → 로그인 화면으로
    console.log('[App] 저장된 사용자 정보 없음 → 로그인 페이지로 이동')
    if (router.currentRoute.value.path !== '/login') {
      router.replace('/login')
    }
  } catch (e) {
    console.error('[App] 자동 로그인 체크 실패:', e)
    if (router.currentRoute.value.path !== '/login') {
      router.replace('/login')
    }
  }
}

// 로그인 상태 및 사용자 ID 변경 감지
let sseUnsubscribers = []  // SSE 구독 해제 함수 목록
let currentMonitoringUserId = null
watch(
  () => userStore.isLoggedIn && userStore.user?.id,
  async (loggedInUserId) => {
    if (loggedInUserId) {
      const userId = loggedInUserId  // string (truthy 확인 후)
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
  // 새 채팅 메시지 알림 (나에게 온 것만)
  const unsubNewChat = sseClient.on('NEW_CHAT', (msg) => {
    const currentUserId = userStore.user?.id
    if (!currentUserId) return
    if (msg.sender_user_id === currentUserId) return  // 내가 보낸 건 제외
    if (msg.target_user_id && msg.target_user_id !== currentUserId) return  // 타겟이 다른 사람

    ElNotification({
      title: '💬 새 메시지',
      message: msg.content?.length > 40 ? msg.content.substring(0, 40) + '...' : msg.content,
      type: 'info',
      duration: 4000,
      position: 'bottom-right'
    })
    // 채팅 실시간 업데이트 이벤트 발행 (ChatView에서 수신)
    window.dispatchEvent(new CustomEvent('bell-new-chat', { detail: msg }))
  })

  // 새 쪽지 / 회의요청 알림 (나에게 온 것만)
  const unsubAnnouncement = sseClient.on('NEW_ANNOUNCEMENT', (data) => {
    const currentUserId = userStore.user?.id
    if (!currentUserId) return
    if (data.sender_user_id === currentUserId) return  // 내가 보낸 건 제외
    if (data.target_user_id && data.target_user_id !== currentUserId) return  // 타겟이 다른 사람

    const isMeeting = data.type === 'meeting'
    const isMail = data.type === 'mail'
    const icon = isMeeting ? '📅' : isMail ? '📧' : '✉️'
    const title = isMeeting ? '회의 요청' : isMail ? '이메일 확인 요청' : '새 쪽지'
    ElNotification({
      title: `${icon} ${title}`,
      message: data.message?.length > 40 ? data.message.substring(0, 40) + '...' : data.message,
      type: isMeeting ? 'warning' : 'success',
      duration: 5000,
      position: 'bottom-right'
    })
    // 인박스 실시간 갱신 이벤트 발행 (InboxListView에서 수신)
    window.dispatchEvent(new CustomEvent('bell-new-inbox', { detail: data }))
  })

  // 사용자 상태 변경 실시간 반영 (전체 대상)
  const unsubUserStatus = sseClient.on('USER_STATUS_CHANGED', (data) => {
    // UserListView가 수신해서 뱃지 즉시 업데이트
    window.dispatchEvent(new CustomEvent('bell-user-status', { detail: data }))
  })

  // 회의 수락/거절 결과 알림 (내가 보낸 회의에 대한 응답)
  const unsubInboxStatus = sseClient.on('INBOX_STATUS_CHANGED', (data) => {
    const currentUserId = userStore.user?.id
    if (!currentUserId) return
    // target_user_id가 나인 경우 (내가 보낸 회의에 상대가 응답)
    if (data.target_user_id && data.target_user_id !== currentUserId) return

    const accepted = data.status === 'accepted'
    ElNotification({
      title: accepted ? '✅ 회의 수락' : '❌ 회의 거절',
      message: accepted ? '상대방이 회의를 수락했습니다.' : '상대방이 회의를 거절했습니다.',
      type: accepted ? 'success' : 'warning',
      duration: 5000,
      position: 'bottom-right'
    })
  })

  // 구독 해제 함수 저장 (onUnmounted에서 정리)
  sseUnsubscribers = [unsubNewChat, unsubAnnouncement, unsubUserStatus, unsubInboxStatus]
}

// 컴포넌트 언마운트 시 정리
onUnmounted(() => {
  stopActivityMonitoring()
  // SSE 리스너 구독 해제
  sseUnsubscribers.forEach(unsub => unsub())
  sseUnsubscribers = []
  sseClient.disconnect()
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

