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
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, TopRight } from '@element-plus/icons-vue'
import { loadMessagesPaged, sendChatMessage, markChatMessageRead } from '@/services/chatService'
import { watchUsers } from '@/services/userService'
import { sseClient } from '@/services/sseClient'
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
let unwatchMessages = null   // SSE 구독 해제 함수

// 사용자 이름 가져오기
const loadUserName = async () => {
  try {
    const currentUserId = userStore.user?.id
    watchUsers((users) => {
      const user = users.find(u => u.id === userId)
      if (user) userName.value = getDisplayName(user)
    }, currentUserId)
  } catch (error) {
    console.error('사용자 정보 로드 실패:', error)
  }
}

// 초기 메시지 로드 (무한 스크롤용 — SSE 도착 전 히스토리)
const loadMessages = async (loadMore = false) => {
  if (loading.value || (!loadMore && messages.value.length > 0)) return

  loading.value = true
  try {
    const currentUserId = userStore.user?.id
    if (!currentUserId) return

    const result = await loadMessagesPaged(userId, currentUserId, 20, loadMore ? lastDoc.value : null)

    if (result.messages && result.messages.length > 0) {
      const converted = result.messages.map(msg => ({
        id: msg.id,
        text: msg.content || '',
        isSent: msg.sender_user_id === currentUserId,
        time: msg.timestamp?.toDate?.()?.toISOString() || msg.timestamp,
        type: msg.type || 'message',
        read: msg.read || false
      }))

      if (loadMore) {
        const prevScrollTop = messagesContainer.value.scrollTop
        const prevScrollHeight = messagesContainer.value.scrollHeight
        messages.value = [...converted, ...messages.value]
        nextTick(() => {
          const newScrollHeight = messagesContainer.value.scrollHeight
          messagesContainer.value.scrollTop = newScrollHeight - prevScrollHeight + prevScrollTop
        })
    } else {
        messages.value = converted
        scrollToBottom()
        // ─── 채팅창 진입 시 수신 메시지 일괄 읽음 처리 ───
        const currentUserId = userStore.user?.id
        const unreadIds = converted
          .filter(m => !m.isSent && !m.read)
          .map(m => m.id)
        if (unreadIds.length > 0 && currentUserId) {
          unreadIds.forEach(id => markChatMessageRead(id))
          // 로컬 상태도 즉시 갱신
          messages.value = messages.value.map(m =>
            !m.isSent && !m.read ? { ...m, read: true } : m
          )
        }
        // ─────────────────────────────────────────────────
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

// 위로 스크롤 시 이전 메시지 로드
const handleScroll = () => {
  if (!messagesContainer.value || loading.value || !hasMore.value) return
  if (messagesContainer.value.scrollTop < 200) loadMessages(true)
}

const sendMessage = async () => {
  if (!inputMessage.value.trim()) return

  const content = inputMessage.value.trim()
  const currentUserId = userStore.user?.id
  if (!currentUserId) return

  // 낙관적 업데이트: 전송 즉시 화면에 표시
  const tempId = `temp-${Date.now()}`
  messages.value.push({
    id: tempId,
    text: content,
    isSent: true,
    time: new Date().toISOString(),
    type: 'message',
    read: false
  })
  inputMessage.value = ''
  scrollToBottom()

  try {
    await sendChatMessage(currentUserId, userId, content)
    // SSE NEW_CHAT 이벤트로 실제 메시지가 도착하면 tempId 메시지는 자동 제거됨
  } catch (error) {
    console.error('메시지 전송 실패:', error)
    messages.value = messages.value.filter(m => m.id !== tempId)
    inputMessage.value = content
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
  const prev = messages.value[index - 1]
  if (!prev?.time || !message.time) return false
  return new Date(message.time).getTime() - new Date(prev.time).getTime() > 5 * 60 * 1000
}

const handleKeyDown = (e) => { if (e.key === 'Escape') router.push('/main') }

onMounted(() => {
  loadUserName()
  loadMessages(false)

  const currentUserId = userStore.user?.id
  if (!currentUserId) return

  // ─── 핵심 수정: SSE 직접 구독 → 전체 재로드 없이 새 메시지 즉시 append ───
  unwatchMessages = sseClient.on('NEW_CHAT', (msg) => {
    // 현재 열린 대화와 관련된 메시지인지 확인
    const isThisChat =
      (msg.sender_user_id === userId && msg.target_user_id === currentUserId) ||
      (msg.sender_user_id === currentUserId && msg.target_user_id === userId)
    if (!isThisChat) return

    // 내가 보낸 메시지이면 낙관적 temp 메시지 제거 (temp-xxx로 시작하는 것만)
    if (msg.sender_user_id === currentUserId) {
      messages.value = messages.value.filter(m => !m.id?.startsWith('temp-'))
    }

    // 이미 있는 메시지 중복 방지 (초기 로드된 것과 겹치는 경우)
    if (messages.value.some(m => m.id === msg.id)) return

    // 새 메시지를 직접 추가 (전체 재로드 없음 → 화면 즉시 반영)
    messages.value.push({
      id: msg.id,
      text: msg.content || '',
      isSent: msg.sender_user_id === currentUserId,
      time: msg.created_at || msg.timestamp || new Date().toISOString(),
      type: msg.type || 'message',
      read: false
    })
    scrollToBottom()

    // 내가 받은 메시지면 즉시 읽음 처리
    if (msg.target_user_id === currentUserId) {
      markChatMessageRead(msg.id)
    }
  })
  // ────────────────────────────────────────────────────────────────────────

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

