<template>
  <div 
    class="chat-room-item px-4 py-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors"
    @click="$emit('click')"
  >
    <div class="flex items-center gap-3">
      <!-- 프로필 이미지/아이콘 -->
      <div 
        v-if="room.icon"
        class="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0"
      >
        <el-icon class="text-blue-600 text-xl">
          <Message v-if="room.icon === 'Message'" />
          <Document v-else-if="room.icon === 'Document'" />
          <VideoCamera v-else-if="room.icon === 'VideoCamera'" />
        </el-icon>
      </div>
      <UserAvatar
        v-else
        :user="roomUser"
        size="12"
        :show-status="false"
      />
      
      <!-- 정보 -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center justify-between mb-0.5">
          <h3 class="font-semibold text-gray-900">{{ room.name }}</h3>
          <div class="flex items-center gap-2">
            <!-- 알림 토글 버튼 -->
            <el-icon
              class="notification-icon cursor-pointer"
              :class="{ 'notification-enabled': notificationEnabled, 'notification-disabled': !notificationEnabled }"
              @click.stop="toggleNotification"
            >
              <Bell v-if="notificationEnabled" />
              <BellFilled v-else />
            </el-icon>
            <span v-if="room.unreadCount > 0" class="unread-badge">{{ room.unreadCount > 99 ? '99+' : room.unreadCount }}</span>
          </div>
        </div>
        <p class="text-sm text-gray-500 truncate">{{ room.lastMessage || room.subtitle || '' }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Message, Document, VideoCamera, Bell, BellFilled } from '@element-plus/icons-vue'
import { getChatNotificationEnabled, setChatNotificationEnabled } from '@/services/chatService'
import { useUserStore } from '@/stores/userStore'
import UserAvatar from '@/components/common/UserAvatar.vue'

const props = defineProps({
  room: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click'])

const userStore = useUserStore()
const notificationEnabled = ref(false)

// room 객체에 user 정보가 포함되어 있으면 사용
const roomUser = computed(() => {
  return props.room.user || null
})

const loadNotificationSetting = async () => {
  const currentUserId = userStore.user?.id
  if (!currentUserId || !props.room.userId) return
  
  try {
    const result = await getChatNotificationEnabled(currentUserId, props.room.userId)
    notificationEnabled.value = result.enabled
  } catch (error) {
    console.error('알림 설정 로드 실패:', error)
  }
}

const toggleNotification = async () => {
  const currentUserId = userStore.user?.id
  if (!currentUserId || !props.room.userId) return
  
  const newValue = !notificationEnabled.value
  try {
    const result = await setChatNotificationEnabled(currentUserId, props.room.userId, newValue)
    if (result.success) {
      notificationEnabled.value = newValue
    }
  } catch (error) {
    console.error('알림 설정 변경 실패:', error)
  }
}

onMounted(() => {
  loadNotificationSetting()
})

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '방금'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}분 전`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}시간 전`
  return date.toLocaleDateString('ko-KR')
}
</script>

<style scoped>
.unread-badge {
  background: #409EFF;
  color: white;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
  line-height: 1.4;
}

.notification-icon {
  font-size: 18px;
  transition: all 0.2s;
}

.notification-enabled {
  color: #409EFF;
}

.notification-disabled {
  color: #d1d5db;
}

.notification-icon:hover {
  transform: scale(1.1);
}
</style>

