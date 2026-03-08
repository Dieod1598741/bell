<template>
  <div class="chat-view h-full flex flex-col bg-white">
    <!-- 헤더 -->
    <div class="header bg-white border-b border-gray-200 px-4 py-6 flex-shrink-0">
      <div class="flex items-center gap-3 relative">
        <el-button 
          :icon="ArrowLeft" 
          circle 
          text
          @click="$router.push('/main')"
          class="text-gray-500 hover:bg-gray-100 -ml-2"
        />
        <div class="absolute left-0 right-0 flex justify-center pointer-events-none">
          <h2 class="text-2xl font-bold text-gray-900">{{ userName }}</h2>
        </div>
        <div class="w-10 h-10 flex-shrink-0"></div>
      </div>
    </div>

    <!-- 메시지 영역 -->
    <div class="flex-1 overflow-y-auto px-4 py-4 space-y-2" ref="messagesContainer">
      <div v-if="loading && messages.length === 0" class="text-center text-gray-400 text-sm py-8">
        로딩 중...
      </div>
      <div v-else-if="messages.length === 0" class="text-center text-gray-400 text-sm py-8">
        메시지가 없습니다.
      </div>
      <div v-if="loading && messages.length > 0" class="text-center text-gray-400 text-sm py-2">
        이전 메시지 로딩 중...
      </div>
      <MessageBubble
        v-for="(message, index) in messages"
        :key="message.id"
        :message="message"
        :show-date="shouldShowDate(message, index)"
      />
      <!-- 타이핑 인디케이터 -->
      <div v-if="isTyping" class="flex justify-start">
        <div class="px-4 py-2.5 rounded-2xl bg-white shadow-sm">
          <div class="flex gap-1">
            <div class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 0s"></div>
            <div class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            <div class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 입력 영역 -->
    <div class="px-4 py-3 border-t border-gray-100 bg-white flex-shrink-0">
      <div class="flex items-center gap-2">
        <el-input
          v-model="inputMessage"
          placeholder="send a message"
          @keyup.enter="sendMessage"
          class="flex-1 message-input"
        />
        <el-button 
          type="primary"
          circle
          @click="sendMessage"
          class="send-button"
        >
          <el-icon>
            <TopRight />
          </el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, TopRight } from '@element-plus/icons-vue'
import { loadMessagesPaged, sendChatMessage, watchMessages, markChatMessageRead } from '@/services/chatService'
import { watchUsers } from '@/services/userService'
import { useUserStore } from '@/stores/userStore'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import { getDisplayName } from '@/utils/userDisplay'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const userId = route.params.userId
const userName = ref('사용자')
const messages = ref([])
const inputMessage = ref('')
const messagesContainer = ref(null)
const isTyping = ref(false)
const loading = ref(false)
const lastDoc = ref(null)
const hasMore = ref(true)
let unwatchMessages = null

// 사용자 이름 가져오기
const loadUserName = async () => {
  try {
    const currentUserId = userStore.user?.id
    watchUsers((users) => {
      const user = users.find(u => u.id === userId)
      if (user) {
        userName.value = getDisplayName(user)
      }
    }, currentUserId)
  } catch (error) {
    console.error('사용자 정보 로드 실패:', error)
  }
}

// 메시지 로드 (무한 스크롤용)
const loadMessages = async (loadMore = false) => {
  if (loading.value || (!loadMore && messages.value.length > 0)) return
  
  loading.value = true
  try {
    const currentUserId = userStore.user?.id
    if (!currentUserId) return
    
    const result = await loadMessagesPaged(userId, currentUserId, 20, loadMore ? lastDoc.value : null)
    
    if (result.messages && result.messages.length > 0) {
      // Firestore 데이터를 MessageBubble 형식으로 변환
      const convertedMessages = result.messages.map(msg => ({
        id: msg.id,
        text: msg.content || '', // content를 text로 변환
        isSent: msg.sender_user_id === currentUserId,
        time: msg.timestamp?.toDate?.()?.toISOString() || msg.timestamp,
        type: msg.type || 'message',
        read: msg.read || false
      }))
      
      if (loadMore) {
        // 이전 메시지 로드 (위에 추가)
        const currentScrollTop = messagesContainer.value.scrollTop
        const currentScrollHeight = messagesContainer.value.scrollHeight
        messages.value = [...convertedMessages, ...messages.value]
        
        // 스크롤 위치 유지
        nextTick(() => {
          const newScrollHeight = messagesContainer.value.scrollHeight
          messagesContainer.value.scrollTop = newScrollHeight - currentScrollHeight + currentScrollTop
        })
      } else {
        // 초기 로드
        messages.value = convertedMessages
        scrollToBottom()
      }
      
      lastDoc.value = result.lastDoc
      hasMore.value = result.hasMore
    } else {
      hasMore.value = false
    }
  } catch (error) {
    console.error('메시지 로드 실패:', error)
  } finally {
    loading.value = false
  }
}

// 스크롤 이벤트 핸들러 (위로 스크롤 시 이전 메시지 로드)
const handleScroll = () => {
  if (!messagesContainer.value || loading.value || !hasMore.value) return
  
  const scrollTop = messagesContainer.value.scrollTop
  // 위에서 200px 이내에 도달하면 이전 메시지 로드
  if (scrollTop < 200) {
    loadMessages(true)
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim()) return
  
  try {
    const currentUserId = userStore.user?.id
    if (!currentUserId) return
    
    await sendChatMessage(currentUserId, userId, inputMessage.value.trim())
    inputMessage.value = ''
    // 메시지 전송 후 최신 메시지 다시 로드 (실시간 리스너로 자동 업데이트되지만 확실하게)
    await loadMessages(false)
  } catch (error) {
    console.error('메시지 전송 실패:', error)
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const shouldShowDate = (message, index) => {
  if (index === 0) return true
  const prevMessage = messages.value[index - 1]
  if (!prevMessage || !prevMessage.time || !message.time) return false
  
  const prevDate = new Date(prevMessage.time)
  const currentDate = new Date(message.time)
  const diff = currentDate.getTime() - prevDate.getTime()
  
  // 5분 이상 차이나면 날짜 표시
  return diff > 5 * 60 * 1000
}

const handleBack = () => {
  router.push('/main')
}

const handleKeyDown = (event) => {
  if (event.key === 'Escape') {
    handleBack()
  }
}

onMounted(() => {
  loadUserName()
  loadMessages(false)
  
  // 실시간 메시지 감시
  const currentUserId = userStore.user?.id
  if (currentUserId) {
    unwatchMessages = watchMessages(userId, currentUserId, (newMessages) => {
      // 읽지 않은 메시지 읽음 처리
      newMessages.forEach(msg => {
        if (!msg.read && msg.target_user_id === currentUserId && msg.sender_user_id === userId) {
          markChatMessageRead(msg.id)
        }
      })
      // Firestore 데이터를 MessageBubble 형식으로 변환
      messages.value = newMessages.map(msg => ({
        id: msg.id,
        text: msg.content || '', // content를 text로 변환
        isSent: msg.sender_user_id === currentUserId,
        time: msg.timestamp?.toDate?.()?.toISOString() || msg.timestamp,
        type: msg.type || 'message',
        read: msg.read || false
      }))
      scrollToBottom()
    })
  }
  
  document.addEventListener('keydown', handleKeyDown)
  if (messagesContainer.value) {
    messagesContainer.value.addEventListener('scroll', handleScroll)
  }
})

onUnmounted(() => {
  if (unwatchMessages) {
    unwatchMessages()
  }
  document.removeEventListener('keydown', handleKeyDown)
  if (messagesContainer.value) {
    messagesContainer.value.removeEventListener('scroll', handleScroll)
  }
})

watch(messages, () => {
  // 새 메시지가 추가되면 맨 아래로 스크롤 (자신이 보낸 메시지인 경우)
  const lastMessage = messages.value[messages.value.length - 1]
  if (lastMessage && lastMessage.sender_user_id === userStore.user?.id) {
    scrollToBottom()
  }
}, { deep: true })
</script>

<style scoped>
.header {
  background: white;
}

.message-input :deep(.el-input__wrapper) {
  box-shadow: none;
  border: none;
  border-radius: 24px;
  padding: 10px 16px;
  background: #f3f4f6;
}

.message-input :deep(.el-input__wrapper:hover) {
  background: #e5e7eb;
}

.message-input :deep(.el-input__wrapper.is-focus) {
  background: white;
  box-shadow: none;
}

.message-input :deep(.el-input__inner) {
  color: #6b7280;
  font-size: 14px;
}

.send-button {
  width: 40px !important;
  height: 40px !important;
  min-width: 40px !important;
  padding: 0 !important;
  border-radius: 50% !important;
  background: #409EFF !important;
  border: none !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  flex-shrink: 0;
  aspect-ratio: 1 / 1;
}

.send-button:hover {
  background: #337ecc !important;
}

.send-button :deep(.el-icon) {
  font-size: 18px !important;
  width: 18px !important;
  height: 18px !important;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-button :deep(svg) {
  width: 18px;
  height: 18px;
}
</style>

