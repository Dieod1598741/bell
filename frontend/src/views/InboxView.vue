<template>
  <div class="inbox-view h-full flex flex-col">
    <!-- 헤더 -->
    <div class="header p-4 shadow-md">
      <div class="flex items-center gap-3">
        <el-button 
          :icon="ArrowLeft" 
          circle 
          @click="$router.push('/main')"
          class="bg-white/20 hover:bg-white/30 border-0"
        />
        <h2 class="font-semibold flex-1 text-white">쪽지함</h2>
      </div>
    </div>

    <!-- 필터 -->
    <div class="p-3 border-b border-gray-200">
      <el-radio-group v-model="filterType" size="small">
        <el-radio-button label="all">전체</el-radio-button>
        <el-radio-button label="meeting">회의</el-radio-button>
        <el-radio-button label="mail">메일</el-radio-button>
        <el-radio-button label="message">쪽지</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 쪽지 목록 -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="filteredInbox.length === 0" class="p-4 text-center text-gray-500">
        쪽지가 없습니다.
      </div>
      <MessageInboxItem
        v-for="item in filteredInbox"
        :key="item.id"
        :item="item"
        @click="openDetail(item)"
        @delete="deleteItem(item.id)"
      />
    </div>

    <!-- 상세 레이어 -->
    <InboxDetailLayer
      v-model:visible="detailVisible"
      :item="selectedItem"
      @reply="handleReply"
      @accept="handleAccept"
      @reject="handleReject"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { backendService } from '@/services/backendService'
import { useUserStore } from '@/stores/userStore'
import MessageInboxItem from '@/components/inbox/MessageInboxItem.vue'
import InboxDetailLayer from '@/components/layers/InboxDetailLayer.vue'

const router = useRouter()
const userStore = useUserStore()
const inbox = ref([])
const filterType = ref('all')
const detailVisible = ref(false)
const selectedItem = ref(null)

const loadInbox = async () => {
  const currentUserId = userStore.user?.id
  if (!currentUserId) return
  try {
    const result = await backendService.getInbox(currentUserId)
    if (result?.success && result.data) {
      inbox.value = result.data.map(msg => ({
        id: msg.id,
        senderId: msg.sender_user_id,
        senderName: msg.sender_name || msg.sender_user_id,
        message: msg.message || msg.content,
        type: msg.type || 'message',
        time: msg.created_at || msg.timestamp,
        read: !!msg.read_at,
        status: msg.status || null
      }))
    }
  } catch (e) {
    console.error('[InboxView] loadInbox 오류:', e)
  }
}

const filteredInbox = computed(() => {
  if (filterType.value === 'all') return inbox.value
  return inbox.value.filter(item => item.type === filterType.value)
})

// 아이템 클릭 → 상세 레이어 + 읽음 처리
const openDetail = async (item) => {
  selectedItem.value = item
  detailVisible.value = true
  // 읽지 않은 경우 읽음 처리
  if (!item.read) {
    try {
      await backendService.markMessageRead(item.id, 'inbox')
      // 로컬에서도 즉시 반영
      const idx = inbox.value.findIndex(m => m.id === item.id)
      if (idx !== -1) inbox.value[idx].read = true
    } catch (e) {
      console.error('[InboxView] markMessageRead 오류:', e)
    }
  }
}

// 답장 → 채팅창으로 이동
const handleReply = (item) => {
  detailVisible.value = false
  router.push(`/chat/${item.senderId}`)
}

// 회의 수락
const handleAccept = async (item) => {
  try {
    await backendService.replyInboxMessage(item.id, 'accepted')
    const idx = inbox.value.findIndex(m => m.id === item.id)
    if (idx !== -1) inbox.value[idx].status = 'accepted'
    if (selectedItem.value?.id === item.id) selectedItem.value = { ...selectedItem.value, status: 'accepted' }
    ElMessage.success('회의를 수락했습니다.')
  } catch (e) {
    ElMessage.error('수락 처리 중 오류가 발생했습니다.')
  }
}

// 회의 거절
const handleReject = async (item) => {
  try {
    await backendService.replyInboxMessage(item.id, 'rejected')
    const idx = inbox.value.findIndex(m => m.id === item.id)
    if (idx !== -1) inbox.value[idx].status = 'rejected'
    if (selectedItem.value?.id === item.id) selectedItem.value = { ...selectedItem.value, status: 'rejected' }
    ElMessage.info('회의를 거절했습니다.')
  } catch (e) {
    ElMessage.error('거절 처리 중 오류가 발생했습니다.')
  }
}

const deleteItem = async (id) => {
  inbox.value = inbox.value.filter(m => m.id !== id)
}

onMounted(() => {
  loadInbox()
})
</script>

<style scoped>
.header {
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
}
</style>
