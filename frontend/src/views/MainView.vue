<template>
  <div class="main-view h-full w-full flex flex-row bg-white">
    <!-- 좌측 사이드바 -->
    <MainSidebar
      v-if="sidebarOpen"
      :active-menu="activeMenu"
      :unread-count="unreadCount"
      :chat-unread-count="chatUnreadCount"
      @menu-change="handleMenuChange"
      @toggle-sidebar="toggleSidebar"
      @open-status="showStatusLayer = true"
      @open-profile="showProfileEditLayer = true"
      @logout="handleLogout"
    />

    <!-- 메인 영역 -->
    <div class="flex-1 flex flex-col relative">
      <UpdateAlert />
      
      <!-- 헤더 -->
      <div class="header bg-white border-b border-gray-200 px-4 py-6">
        <div class="flex items-center gap-3">
          <h1 class="text-2xl font-bold text-gray-900 flex-1">{{ headerTitle }}</h1>
        </div>
      </div>

      <!-- 검색 바 (채팅 메뉴일 때만) -->
      <div v-if="activeMenu === 'chat'" class="px-4 py-2 border-b border-gray-100">
        <el-input
          v-model="searchQuery"
          placeholder="Search for contacts"
          class="search-input"
          size="small"
        >
          <template #prefix>
            <el-icon class="text-gray-400 text-sm"><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- 컨텐츠 영역 -->
      <div class="flex-1 overflow-y-auto relative">
        <ChatRoomList
          v-if="activeMenu === 'chat'"
          :search-query="searchQuery"
        />
        <UserListView
          v-else-if="activeMenu === 'users'"
          :selected-user-id="selectedUserId"
        />
        <InboxListView
          v-else-if="activeMenu === 'inbox'"
        />
      </div>
      
      <!-- 사이드바 닫혔을 때 왼쪽 하단 햄버거 버튼 (고정 위치) -->
      <div
        v-if="!sidebarOpen"
        class="hamburger-button-fixed"
        @click="toggleSidebar"
      >
        <div class="w-12 h-12 rounded-lg bg-blue-500 flex items-center justify-center cursor-pointer hover:bg-blue-600 transition-colors shadow-lg">
          <div class="hamburger-icon flex flex-col gap-1.5">
            <span class="w-5 h-0.5 bg-white rounded"></span>
            <span class="w-5 h-0.5 bg-white rounded"></span>
            <span class="w-5 h-0.5 bg-white rounded"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 상태 설정 레이어 -->
    <StatusLayer
      :visible="showStatusLayer"
      @update:visible="showStatusLayer = $event"
      @logout="handleLogout"
    />

    <!-- 프로필 수정 레이어 -->
    <ProfileEditLayer
      :visible="showProfileEditLayer"
      @update:visible="showProfileEditLayer = $event"
    />

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import MainSidebar from '@/components/common/MainSidebar.vue'
import ChatRoomList from '@/components/chat/ChatRoomList.vue'
import UserListView from '@/components/user/UserListView.vue'
import InboxListView from '@/components/inbox/InboxListView.vue'
import StatusLayer from '@/components/layers/StatusLayer.vue'
import ProfileEditLayer from '@/components/layers/ProfileEditLayer.vue'
import UpdateAlert from '@/components/common/UpdateAlert.vue'
import { watchInbox } from '@/services/inboxService'
import { watchChats } from '@/services/chatService'
import { watchAnnouncements } from '@/services/announcementService'
import { loadUsers } from '@/services/userService'
import { useUserStore } from '@/stores/userStore'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const handleLogout = async () => {
  await userStore.logout()
  router.push('/login')
}
const activeMenu = ref('chat')
const searchQuery = ref('')
const unreadCount = ref(0) // 인박스 읽지 않은 개수
const chatUnreadCount = ref(0) // 채팅 읽지 않은 개수
const sidebarOpen = ref(true)
const showStatusLayer = ref(false)
const showProfileEditLayer = ref(false)
const selectedUserId = ref(null)
let unwatchInbox = null
let unwatchChats = null
let unwatchAnnouncements = null

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
}

const headerTitle = computed(() => {
  switch (activeMenu.value) {
    case 'chat':
      return 'Contact'
    case 'users':
      return 'Users'
    case 'inbox':
      return 'Inbox'
    default:
      return 'Contact'
  }
})

const handleMenuChange = (menu) => {
  activeMenu.value = menu
  searchQuery.value = ''
}

// 백엔드에 알림 요청
const requestBackendNotification = async (title, message, notificationType, senderName = null) => {
  try {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.showNotification) {
      const result = await window.pywebview.api.showNotification(title, message, notificationType, senderName)
      if (result && result.success === false) {
        console.error('[MainView] 백엔드 알림 요청 실패:', result.error)
      }
    } else {
      console.warn('[MainView] 백엔드 API를 사용할 수 없습니다. 브라우저 알림으로 대체합니다.')
      // 백엔드 API가 없으면 브라우저 알림으로 대체
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, { body: message })
      }
    }
  } catch (error) {
    console.error('[MainView] 알림 요청 오류:', error)
  }
}

// 알림 제목 및 내용 생성
const getNotificationTitle = (type, senderName) => {
  const titles = {
    'meeting': '📅 회의 요청',
    'mail': '📧 메일 확인 요청',
    'message': '💬 쪽지',
    'note': '💬 쪽지'
  }
  return titles[type] || '🔔 알림'
}

// 실시간 읽지 않은 개수 업데이트 및 알림 표시
let previousInboxMessages = []
let previousAnnouncements = []
const setupUnreadCountWatchers = () => {
  const currentUserId = userStore.user?.id
  if (!currentUserId) return
  
  // 인박스 읽지 않은 개수 감시 및 새 메시지 알림
  unwatchInbox = watchInbox(currentUserId, (messages) => {
    unreadCount.value = messages.filter(m => !m.read).length
    
    // 새 메시지 감지 (이전에 없던 메시지)
    const newMessages = messages.filter(msg => {
      return !previousInboxMessages.some(prev => prev.id === msg.id)
    })
    
    // 새 메시지가 있으면 알림 표시
    if (newMessages.length > 0 && previousInboxMessages.length > 0) {
      newMessages.forEach(async (msg) => {
        // 사용자 정보 가져오기 (발신자 이름)
        const result = await loadUsers(1000)
        const sender = result.users.find(u => u.id === msg.sender_user_id)
        const senderName = sender ? (sender.nickNm || sender.name) : msg.sender_user_id
        const title = getNotificationTitle(msg.type, senderName)
        const content = msg.content || ''
        const message = content.length > 100 ? content.substring(0, 100) + '...' : content
        
        // 백엔드에 알림 요청
        await requestBackendNotification(title, message, msg.type || 'message', senderName)
      })
    }
    
    previousInboxMessages = [...messages]
  })
  
  // 채팅 읽지 않은 개수 감시 및 새 메시지 알림
  let previousChatMessages = []
  unwatchChats = watchChats(currentUserId, (messages) => {
    // 각 사용자별로 읽지 않은 메시지 개수 계산
    const unreadByUser = new Map()
    messages.forEach(m => {
      if (!m.read && m.target_user_id === currentUserId) {
        const senderId = m.sender_user_id
        unreadByUser.set(senderId, (unreadByUser.get(senderId) || 0) + 1)
      }
    })
    chatUnreadCount.value = Array.from(unreadByUser.values()).reduce((sum, count) => sum + count, 0)
    
    // 새 메시지 감지 (이전에 없던 메시지)
    const newMessages = messages.filter(msg => {
      return !msg.read && 
             msg.target_user_id === currentUserId &&
             !previousChatMessages.some(prev => prev.id === msg.id)
    })
    
    // 새 메시지가 있으면 알림 표시
    if (newMessages.length > 0 && previousChatMessages.length > 0) {
      newMessages.forEach(async (msg) => {
        // 사용자 정보 가져오기 (발신자 이름)
        const result = await loadUsers(1000)
        const sender = result.users.find(u => u.id === msg.sender_user_id)
        const senderName = sender ? (sender.nickNm || sender.name) : msg.sender_user_id
        const content = msg.content || ''
        const message = content.length > 100 ? content.substring(0, 100) + '...' : content
        
        // 백엔드에 알림 요청
        await requestBackendNotification(`💬 ${senderName}`, message, 'message', senderName)
      })
    }
    
    previousChatMessages = [...messages]
  })
  
  // 알람 감시 및 새 알람 알림
  unwatchAnnouncements = watchAnnouncements(currentUserId, (announcements) => {
    // 첫 로드인지 확인
    const isFirstLoad = previousAnnouncements.length === 0
    
    // 새 알람 감지 (이전에 없던 알람)
    const newAnnouncements = announcements.filter(ann => {
      return !previousAnnouncements.some(prev => prev.id === ann.id)
    })
    
    // 새 알람이 있으면 알림 표시 (첫 로드가 아닌 경우에만 - 이미 있는 알림은 제외)
    if (newAnnouncements.length > 0 && !isFirstLoad) {
      newAnnouncements.forEach(async (ann) => {
        const title = 'Bell'
        const content = ann.message || ''
        const message = content.length > 100 ? content.substring(0, 100) + '...' : content
        
        console.log('[MainView] 새 알람 감지, 알림 전송:', title, message)
        // 백엔드에 알림 요청
        await requestBackendNotification(title, message, 'announcement')
      })
    }
    
    // 이전 알람 목록 업데이트
    previousAnnouncements = [...announcements]
  })
}

onMounted(async () => {
  if (!userStore.isLoggedIn || !userStore.user) {
    console.log('[MainView] 로그인 상태 없음 - 로그인 페이지로 이동')
    router.push('/login')
    return
  }
  
  console.log('[MainView] 사용자 확인 완료: user_id=', userStore.user?.id)
  
  if (route.query.selectedUserId) {
    selectedUserId.value = route.query.selectedUserId
    activeMenu.value = 'users'
    router.replace({ query: {} })
  }
  setupUnreadCountWatchers()

  // 백엔드 DB 기준 정확한 count 실시간 반영 (2초 폴링)
  window.addEventListener('bell-unread-count', _onUnreadCount)
})

const _onUnreadCount = (e) => {
  // DB 기준 완전한 미읽음 count를 unreadCount에 즈시 반영
  const count = e.detail?.count
  if (typeof count === 'number') {
    unreadCount.value = count
  }
}

onUnmounted(() => {
  if (unwatchInbox) unwatchInbox()
  if (unwatchChats) unwatchChats()
  if (unwatchAnnouncements) unwatchAnnouncements()
  window.removeEventListener('bell-unread-count', _onUnreadCount)
})

</script>

<style scoped>
.header {
  background: white;
}

.search-input :deep(.el-input__wrapper) {
  box-shadow: none;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 6px 12px;
  background: #f9fafb;
  min-height: 36px;
}

.search-input :deep(.el-input__wrapper:hover) {
  border-color: #d1d5db;
  background: white;
}

.search-input :deep(.el-input__wrapper.is-focus) {
  border-color: #409EFF;
  background: white;
}

.hamburger-button-fixed {
  position: fixed;
  left: 16px;
  bottom: 16px;
  z-index: 20;
}

/* #app의 max-width를 고려한 위치 조정 */
@media (min-width: 450px) {
  .hamburger-button-fixed {
    left: calc((100vw - 450px) / 2 + 8px);
  }
}
</style>

