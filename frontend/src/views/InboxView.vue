<template>
  <div class="inbox-view h-full flex flex-col">
    <!-- 헤더 -->
    <div class="header bg-gradient-to-r from-primary to-primary-light text-white p-4 shadow-md">
      <div class="flex items-center gap-3">
        <el-button 
          :icon="ArrowLeft" 
          circle 
          @click="$router.push('/main')"
          class="bg-white/20 hover:bg-white/30 border-0"
        />
        <h2 class="font-semibold flex-1">쪽지함</h2>
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
        @click="openChat(item.senderId)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { watchInbox } from '@/services/inboxService'
import { useUserStore } from '@/stores/userStore'
import MessageInboxItem from '@/components/inbox/MessageInboxItem.vue'

const router = useRouter()
const userStore = useUserStore()
const inbox = ref([])
const filterType = ref('all')

const loadInbox = () => {
  const currentUserId = userStore.user?.id
  if (!currentUserId) return
  
  watchInbox(currentUserId, (messages) => {
    inbox.value = messages.map(msg => ({
      id: msg.id,
      senderId: msg.sender_user_id,
      senderName: msg.sender_name || msg.sender_user_id,
      message: msg.message || msg.content,
      type: msg.type || 'message',
      time: msg.timestamp?.toDate?.()?.toISOString() || msg.timestamp,
      read: msg.read || false
    }))
  })
}

const filteredInbox = computed(() => {
  if (filterType.value === 'all') return inbox.value
  return inbox.value.filter(item => item.type === filterType.value)
})

const openChat = (userId) => {
  router.push(`/chat/${userId}`)
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

