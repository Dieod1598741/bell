<template>
  <div class="chat-room-list">
    <!-- 로딩 스켈레톤 -->
    <div v-if="isLoading" class="skeleton-list">
      <div v-for="i in 5" :key="i" class="skeleton-item">
        <div class="skeleton-avatar"></div>
        <div class="skeleton-content">
          <div class="skeleton-line wide"></div>
          <div class="skeleton-line narrow"></div>
        </div>
      </div>
    </div>
    <!-- 빈 상태: 로드 완료 후에만 표시 -->
    <div v-else-if="filteredRooms.length === 0" class="empty-state">
      <p class="text-gray-400 text-sm">{{ searchQuery ? '검색 결과가 없습니다' : '최근 대화가 없습니다' }}</p>
    </div>
    <div v-else>
      <ChatRoomItem
        v-for="room in sortedRooms"
        :key="room.userId"
        :room="room"
        @click="openChat(room.userId)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { watchUsers } from '@/services/userService'
import { watchChats } from '@/services/chatService'
import { useUserStore } from '@/stores/userStore'
import ChatRoomItem from '@/components/chat/ChatRoomItem.vue'

const props = defineProps({
  searchQuery: {
    type: String,
    default: ''
  }
})

const router = useRouter()
const userStore = useUserStore()
const chatRooms = ref([])
const isLoading = ref(true)

let unsubscribeUsers = null
let unsubscribeChats = null

const updateChatRooms = (users, messages) => {
  const currentUserId = userStore.user?.id
  if (!currentUserId) return
  
  // 각 사용자별로 최근 메시지 찾기
  const rooms = users.map(user => {
    const userMessages = messages.filter(m => 
      (m.sender_user_id === user.id && m.target_user_id === currentUserId) ||
      (m.sender_user_id === currentUserId && m.target_user_id === user.id)
    )
    const lastMessage = userMessages[0] // 이미 시간순 정렬됨
    
    if (lastMessage) {
      // 마지막 메시지가 길면 30자로 제한
      const messageContent = lastMessage.content || ''
      const truncatedMessage = messageContent.length > 30 
        ? messageContent.substring(0, 30) + '...' 
        : messageContent
      
      return {
        userId: user.id,
        user: user, // 사용자 전체 정보 포함
        name: user.nickNm || user.name, // 닉네임 우선
        subtitle: '', // 이메일 대신 빈 문자열
        lastMessage: truncatedMessage,
        lastMessageTime: lastMessage.timestamp?.toDate?.()?.toISOString() || lastMessage.timestamp,
        unreadCount: messages.filter(m => 
          m.sender_user_id === user.id && 
          m.target_user_id === currentUserId &&
          !m.read
        ).length
      }
    }
    return null
  }).filter(Boolean)
  
  // 시간순 정렬
  rooms.sort((a, b) => {
    const timeA = a.lastMessageTime ? new Date(a.lastMessageTime).getTime() : 0
    const timeB = b.lastMessageTime ? new Date(b.lastMessageTime).getTime() : 0
    return timeB - timeA
  })
  
  chatRooms.value = rooms
  isLoading.value = false
}

const loadChatRooms = () => {
  const currentUserId = userStore.user?.id
  if (!currentUserId) return
  
  let users = []
  let messages = []
  
  unsubscribeUsers = watchUsers((userList) => {
    users = userList
    updateChatRooms(users, messages)
  }, currentUserId)
  
  unsubscribeChats = watchChats(currentUserId, (messageList) => {
    messages = messageList
    updateChatRooms(users, messages)
  })
}

const filteredRooms = computed(() => {
  if (!props.searchQuery) return chatRooms.value
  const query = props.searchQuery.toLowerCase()
  return chatRooms.value.filter(room => 
    room.name?.toLowerCase().includes(query) ||
    room.subtitle?.toLowerCase().includes(query)
  )
})

const sortedRooms = computed(() => {
  // 이미 시간순 정렬되어 있음
  return filteredRooms.value
})

const openChat = (userId) => {
  router.push(`/chat/${userId}`)
}

onMounted(() => {
  loadChatRooms()
})

onUnmounted(() => {
  if (unsubscribeUsers) unsubscribeUsers()
  if (unsubscribeChats) unsubscribeChats()
})
</script>

<style scoped>
.chat-room-list {
  height: 100%;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

/* 스켈레톤 로딩 */
.skeleton-list {
  padding: 8px 0;
}
.skeleton-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
}
.skeleton-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
  flex-shrink: 0;
}
.skeleton-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.skeleton-line {
  height: 12px;
  border-radius: 6px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
}
.skeleton-line.wide { width: 70%; }
.skeleton-line.narrow { width: 45%; }
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

</style>
