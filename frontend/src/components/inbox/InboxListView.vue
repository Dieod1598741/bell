<template>
  <div class="inbox-list-view">
    <!-- 필터 및 모두 읽음 버튼 -->
    <div class="filter-tabs px-4 py-3 border-b border-gray-100 flex items-center justify-between">
      <div class="flex gap-2">
        <button
          v-for="filter in filters"
          :key="filter.value"
          class="filter-tab"
          :class="{ active: filterType === filter.value }"
          @click="filterType = filter.value"
        >
          {{ filter.label }}
        </button>
      </div>
      <el-button 
        link
        size="small"
        @click="markAllAsRead"
        :disabled="unreadCount === 0"
        class="text-xs"
      >
        모두 읽음
      </el-button>
    </div>

    <!-- 메시지 목록 -->
    <div ref="listContainer" class="flex-1 overflow-y-auto">
      <!-- 로딩 스켈레톤 -->
      <div v-if="isLoading" class="skeleton-list">
        <div v-for="i in 5" :key="i" class="skeleton-msg">
          <div class="skeleton-icon"></div>
          <div class="skeleton-body">
            <div class="skeleton-line wide"></div>
            <div class="skeleton-line narrow"></div>
          </div>
        </div>
      </div>
      <div v-else-if="filteredInbox.length === 0" class="empty-state">
        <p class="text-gray-400 text-sm">메시지가 없습니다</p>
      </div>
      <MessageInboxItem
        v-for="item in filteredInbox"
        :key="item.id"
        :item="item"
        @click="openDetail(item)"
        @delete="handleDelete"
      />
    </div>

    <!-- 상세 레이어 -->
    <InboxDetailLayer
      :visible="showDetailLayer"
      :item="selectedItem"
      @update:visible="showDetailLayer = $event"
      @reply="handleReply"
      @accept="handleAccept"
      @reject="handleReject"
    />
    
    <!-- 답장 레이어 -->
    <NoteLayer
      :visible="showReplyLayer"
      :user-id="replyTargetId"
      @update:visible="showReplyLayer = $event"
      @submit="handleReplySubmit"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { watchInbox, markMessageRead, markAllInboxAsRead, deleteInboxMessage, sendInboxMessage } from '@/services/inboxService'
import { loadUsers } from '@/services/userService'
import { backendService } from '@/services/backendService'
import MessageInboxItem from '@/components/inbox/MessageInboxItem.vue'
import InboxDetailLayer from '@/components/layers/InboxDetailLayer.vue'
import NoteLayer from '@/components/layers/NoteLayer.vue'
import { useUserStore } from '@/stores/userStore'

const userStore = useUserStore()
const listContainer = ref(null)
const filterType = ref('all')
const showDetailLayer = ref(false)
const showReplyLayer = ref(false)
const selectedItem = ref(null)
const replyTargetId = ref(null)
const allInbox = ref([])
const isLoading = ref(true)
let unwatchInbox = null
let inboxHandler = null  // 로컬 변수로 변경 (window 글로벌 오염 방지)

const filters = [
  { value: 'all', label: '전체' },
  { value: 'meeting', label: '회의' },
  { value: 'mail', label: '메일' },
  { value: 'message', label: '쪽지' }
]

// 실시간 인박스 감시
onMounted(async () => {
  const currentUserId = userStore.user?.id
  if (currentUserId) {
    // 사용자 목록 미리 로드
    const usersResult = await loadUsers(1000)
    const usersMap = new Map(usersResult.users.map(u => [u.id, u]))
    
    unwatchInbox = watchInbox(currentUserId, (messages) => {
      allInbox.value = messages.map(msg => {
        const sender = usersMap.get(msg.sender_user_id)
        return {
          id: msg.id,
          senderId: msg.sender_user_id,
          senderName: sender ? (sender.nickNm || sender.name) : msg.sender_user_id,
          message: msg.content || '',
          type: msg.type || 'message',
          time: msg.timestamp?.toDate?.()?.toISOString() || msg.timestamp,
          read: msg.read || false
        }
      })
      isLoading.value = false
    })

    // SSE: 새 인박스 메시지 실시간 추가
    const handleNewInbox = (e) => {
      const data = e.detail || {}
      if (!data.id) return
      const already = allInbox.value.find(m => m.id === data.id)
      if (already) return
      const sender = usersMap.get(data.sender_user_id)
      allInbox.value.unshift({
        id: data.id,
        senderId: data.sender_user_id,
        senderName: sender ? (sender.nickNm || sender.name) : data.sender_user_id,
        message: data.message || '',
        type: data.type || 'message',
        time: new Date().toISOString(),
        read: false
      })
    }
    inboxHandler = handleNewInbox
    window.addEventListener('bell-new-inbox', inboxHandler)
  }
})

onUnmounted(() => {
  if (unwatchInbox) {
    unwatchInbox()
  }
  if (inboxHandler) {
    window.removeEventListener('bell-new-inbox', inboxHandler)
    inboxHandler = null
  }
})

const filteredInbox = computed(() => {
  if (filterType.value === 'all') return allInbox.value
  // 'message'와 'note' 모두 쪽지로 필터링
  if (filterType.value === 'message') {
    return allInbox.value.filter(item => item.type === 'message' || item.type === 'note')
  }
  return allInbox.value.filter(item => item.type === filterType.value)
})

// 필터 변경 시 리셋 (선택사항)
watch(filterType, () => {
  // 필터 변경 시에는 리셋하지 않고 클라이언트 사이드에서 필터링만 수행
})

const unreadCount = computed(() => {
  return allInbox.value.filter(item => !item.read).length
})

const markAllAsRead = async () => {
  try {
    const unreadItems = allInbox.value.filter(item => !item.read)
    await markAllInboxAsRead(unreadItems.map(item => item.id))
  } catch (error) {
    console.error('모두 읽음 처리 실패:', error)
  }
}

const handleDelete = async (itemId) => {
  try {
    await deleteInboxMessage(itemId)
  } catch (error) {
    console.error('메시지 삭제 실패:', error)
  }
}

const handleReply = (item) => {
  replyTargetId.value = item.senderId
  showDetailLayer.value = false
  showReplyLayer.value = true
}

const handleReplySubmit = async (data) => {
  try {
    const currentUserId = userStore.user?.id
    if (!currentUserId) return
    
    await sendInboxMessage(currentUserId, data.userId, data.message, 'note')
    showReplyLayer.value = false
    ElMessage.success('답장이 전송되었습니다')
  } catch (error) {
    console.error('답장 전송 실패:', error)
    ElMessage.error('답장 전송에 실패했습니다')
  }
}

const handleAccept = async (item) => {
  try {
    await backendService.replyInboxMessage(item.id, 'accepted')
    const idx = allInbox.value.findIndex(m => m.id === item.id)
    if (idx !== -1) allInbox.value[idx].status = 'accepted'
    if (selectedItem.value?.id === item.id) selectedItem.value = { ...selectedItem.value, status: 'accepted' }
    ElMessage.success('회의를 수락했습니다.')
  } catch (e) {
    ElMessage.error('수락 처리 중 오류가 발생했습니다.')
  }
}

const handleReject = async (item) => {
  try {
    await backendService.replyInboxMessage(item.id, 'rejected')
    const idx = allInbox.value.findIndex(m => m.id === item.id)
    if (idx !== -1) allInbox.value[idx].status = 'rejected'
    if (selectedItem.value?.id === item.id) selectedItem.value = { ...selectedItem.value, status: 'rejected' }
    ElMessage.info('회의를 거절했습니다.')
  } catch (e) {
    ElMessage.error('거절 처리 중 오류가 발생했습니다.')
  }
}

const openDetail = async (item) => {
  selectedItem.value = item
  showDetailLayer.value = true
  if (!item.read) {
    await markMessageRead(item.id, 'inbox')
    item.read = true
  }
}
</script>

<style scoped>
.inbox-list-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.filter-tabs {
  background: white;
}

.filter-tab {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-tab:hover {
  color: #374151;
  background: #f3f4f6;
}

.filter-tab.active {
  color: #409EFF;
  background: #ecf5ff;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

/* 스켈레톤 */
.skeleton-list { padding: 8px 0; }
.skeleton-msg { display: flex; align-items: center; gap: 12px; padding: 14px 16px; border-bottom: 1px solid #f3f4f6; }
.skeleton-icon { width: 36px; height: 36px; border-radius: 8px; background: linear-gradient(90deg,#f0f0f0 25%,#e0e0e0 50%,#f0f0f0 75%); background-size: 200% 100%; animation: shimmer 1.2s infinite; flex-shrink: 0; }
.skeleton-body { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.skeleton-line { height: 11px; border-radius: 6px; background: linear-gradient(90deg,#f0f0f0 25%,#e0e0e0 50%,#f0f0f0 75%); background-size: 200% 100%; animation: shimmer 1.2s infinite; }
.skeleton-line.wide { width: 60%; }
.skeleton-line.narrow { width: 80%; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
</style>

