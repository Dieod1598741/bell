<template>
  <ActionLayer :visible="visible" @update:visible="$emit('update:visible', $event)">
    <div class="announcement-layer">
      <h3 class="text-xl font-bold mb-6">알람</h3>
      
      <div v-if="announcements.length === 0" class="empty-state">
        <p class="text-gray-400 text-sm">알람이 없습니다</p>
      </div>
      
      <div v-else class="announcement-list">
        <div
          v-for="announcement in announcements"
          :key="announcement.id"
          class="announcement-item"
          :class="{ 'unread': !announcement.read }"
          @click="handleAnnouncementClick(announcement)"
        >
          <div class="announcement-content">
            <div class="announcement-header">
              <div class="announcement-title">관리자 알람</div>
              <div class="announcement-time">
                {{ formatTime(announcement.timestamp) }}
              </div>
            </div>
            <div class="announcement-message">
              {{ announcement.message }}
            </div>
          </div>
          <div v-if="!announcement.read" class="unread-indicator"></div>
        </div>
      </div>
    </div>
  </ActionLayer>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { watchAnnouncements, markAnnouncementRead } from '@/services/announcementService'
import { useUserStore } from '@/stores/userStore'
import ActionLayer from '@/components/layers/ActionLayer.vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible'])

const userStore = useUserStore()

const announcements = ref([])
let unwatchAnnouncements = null

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  
  const date = timestamp.toDate ? timestamp.toDate() : new Date(timestamp)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '방금 전'
  if (minutes < 60) return `${minutes}분 전`
  if (hours < 24) return `${hours}시간 전`
  if (days < 7) return `${days}일 전`
  
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const handleAnnouncementClick = async (announcement) => {
  if (!announcement.read) {
    await markAnnouncementRead(announcement.id)
  }
}

const loadAnnouncements = () => {
  const currentUserId = userStore.user?.id
  if (!currentUserId) return
  
  if (unwatchAnnouncements) {
    unwatchAnnouncements()
  }
  
  unwatchAnnouncements = watchAnnouncements(currentUserId, (announcementsList) => {
    announcements.value = announcementsList
  })
}

onMounted(() => {
  if (props.visible) {
    loadAnnouncements()
  }
})

onUnmounted(() => {
  if (unwatchAnnouncements) {
    unwatchAnnouncements()
  }
})

watch(() => props.visible, (newVal) => {
  if (newVal) {
    loadAnnouncements()
  }
})
</script>

<style scoped>
.announcement-layer {
  padding: 20px 0;
  max-height: 80vh;
  overflow-y: auto;
}

.announcement-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.announcement-item {
  position: relative;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.announcement-item:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.announcement-item.unread {
  background: #f0f9ff;
  border-color: #409EFF;
}

.announcement-content {
  flex: 1;
  min-width: 0;
}

.announcement-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.announcement-title {
  font-weight: 600;
  font-size: 15px;
  color: #111827;
}

.announcement-time {
  font-size: 12px;
  color: #6b7280;
}

.announcement-message {
  font-size: 14px;
  color: #374151;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.unread-indicator {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 8px;
  height: 8px;
  background: #409EFF;
  border-radius: 50%;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}
</style>

