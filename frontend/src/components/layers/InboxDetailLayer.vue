<template>
  <ActionLayer :visible="visible" @update:visible="$emit('update:visible', $event)">
    <div class="inbox-detail-layer">
      <div class="header-section">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-12 h-12 rounded-full bg-blue-500 flex items-center justify-center text-white flex-shrink-0">
            <el-icon v-if="item?.type === 'meeting'" class="text-xl">
              <Calendar />
            </el-icon>
            <el-icon v-else-if="item?.type === 'mail'" class="text-xl">
              <Message />
            </el-icon>
            <el-icon v-else class="text-xl">
              <ChatDotRound />
            </el-icon>
          </div>
          <div class="flex-1">
            <h3 class="text-lg font-bold text-gray-900">{{ item?.senderName }}</h3>
            <p class="text-sm text-gray-500">{{ getTypeLabel(item?.type) }}</p>
          </div>
          <span class="text-xs text-gray-400">{{ formatTime(item?.time) }}</span>
        </div>
      </div>
      
      <div class="content-section">
        <div class="message-content">
          <template v-if="item?.type === 'meeting'">
            <div class="meeting-details">
              <div v-if="parsedMeeting.time" class="detail-item">
                <span class="detail-label">시간</span>
                <div class="detail-value-box">
                  <span class="detail-value">{{ parsedMeeting.time }}</span>
                </div>
              </div>
              <div v-if="parsedMeeting.place" class="detail-item">
                <span class="detail-label">장소</span>
                <div class="detail-value-box">
                  <span class="detail-value" v-html="formatLink(parsedMeeting.place)"></span>
                </div>
              </div>
              <div v-if="parsedMeeting.memo" class="detail-item">
                <span class="detail-label">메모</span>
                <div class="detail-value-box">
                  <span class="detail-value">{{ parsedMeeting.memo }}</span>
                </div>
              </div>
            </div>
          </template>
          <template v-else>
            <div class="message-text" v-html="formatMessage(item?.message, item?.type)"></div>
          </template>
        </div>
      </div>
      
      <!-- 회의 수락/거절 버튼 (회의 요청인 경우) -->
      <div v-if="item?.type === 'meeting'" class="action-section mt-4">
        <div class="flex gap-3">
          <el-button
            type="success"
            class="flex-1"
            :disabled="item?.status === 'accepted'"
            @click="$emit('accept', item)"
          >
            {{ item?.status === 'accepted' ? '✅ 수락됨' : '수락' }}
          </el-button>
          <el-button
            type="danger"
            class="flex-1"
            :disabled="item?.status === 'rejected'"
            @click="$emit('reject', item)"
          >
            {{ item?.status === 'rejected' ? '❌ 거절됨' : '거절' }}
          </el-button>
        </div>
      </div>

      <!-- 답장 버튼 (쪽지인 경우만) -->
      <div v-if="item?.type === 'message' || item?.type === 'note'" class="reply-section mt-4">
        <el-button 
          type="primary" 
          class="w-full"
          @click="$emit('reply', item)"
        >
          답장
        </el-button>
      </div>
    </div>
  </ActionLayer>
</template>

<script setup>
import { computed } from 'vue'
import { Calendar, Message, ChatDotRound } from '@element-plus/icons-vue'
import ActionLayer from '@/components/layers/ActionLayer.vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  item: {
    type: Object,
    default: null
  }
})

defineEmits(['update:visible', 'reply', 'accept', 'reject', 'markRead'])

const getTypeLabel = (type) => {
  const labels = {
    meeting: '회의 요청',
    mail: '메일 확인 요청',
    message: '쪽지'
  }
  return labels[type] || '메시지'
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '방금'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}분 전`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}시간 전`
  return date.toLocaleDateString('ko-KR', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const parsedMeeting = computed(() => {
  if (!props.item || props.item.type !== 'meeting' || !props.item.message) {
    return { time: '', place: '', memo: '' }
  }
  
  const message = props.item.message
  const lines = message.split('\n').map(line => line.trim()).filter(line => line)
  
  let time = ''
  let place = ''
  let memo = ''
  
  lines.forEach(line => {
    if (line.startsWith('시간:')) {
      time = line.replace('시간:', '').trim()
    } else if (line.startsWith('장소:')) {
      place = line.replace('장소:', '').trim()
    } else if (line.startsWith('메모:')) {
      memo = line.replace('메모:', '').trim()
    }
  })
  
  return { time, place, memo }
})

const formatLink = (text) => {
  if (!text) return ''
  
  // 전체 텍스트가 http:// 또는 https://로 시작하는 경우
  if (text.startsWith('http://') || text.startsWith('https://')) {
    return `<a href="${text}" target="_blank" rel="noopener noreferrer" class="message-link">${text}</a>`
  }
  
  // www.로 시작하는 경우
  if (text.startsWith('www.')) {
    const href = 'https://' + text
    return `<a href="${href}" target="_blank" rel="noopener noreferrer" class="message-link">${text}</a>`
  }
  
  // 텍스트 내에 URL이 포함된 경우
  const urlPattern = /(https?:\/\/[^\s]+|www\.[^\s]+)/gi
  return text.replace(urlPattern, (url) => {
    let href = url
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      href = 'https://' + url
    }
    return `<a href="${href}" target="_blank" rel="noopener noreferrer" class="message-link">${url}</a>`
  })
}

const formatMessage = (message, type) => {
  if (!message) return ''
  
  // 줄바꿈 유지
  let formatted = message.replace(/\n/g, '<br>')
  
  // URL 패턴 감지 (http://, https://, www.로 시작하는 링크)
  const urlPattern = /(https?:\/\/[^\s]+|www\.[^\s]+)/gi
  formatted = formatted.replace(urlPattern, (url) => {
    let href = url
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      href = 'https://' + url
    }
    return `<a href="${href}" target="_blank" rel="noopener noreferrer" class="message-link">${url}</a>`
  })
  
  return formatted
}
</script>

<style scoped>
.inbox-detail-layer {
  padding: 0;
}

.header-section {
  padding-bottom: 20px;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 20px;
}

.content-section {
  min-height: 200px;
  padding: 8px 0;
}

.message-content {
  background: #f9fafb;
  border-radius: 12px;
  padding: 32px 28px;
  min-height: 180px;
}

.message-text {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
  font-size: 16px;
  line-height: 1.8;
  color: #374151;
  word-wrap: break-word;
  margin: 0;
  letter-spacing: 0.2px;
}

.message-link {
  color: #2563eb;
  text-decoration: none;
  cursor: pointer;
  transition: color 0.2s;
  font-weight: 500;
}

.message-link:hover {
  color: #1d4ed8;
  text-decoration: underline;
}

.meeting-details {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-label {
  font-size: 12px;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value-box {
  padding: 0;
}

.detail-value {
  font-size: 16px;
  color: #111827;
  line-height: 1.7;
  font-weight: 400;
}

.detail-value :deep(.message-link) {
  color: #2563eb !important;
  text-decoration: none;
  font-weight: 500;
}

.detail-value :deep(.message-link:hover) {
  color: #1d4ed8 !important;
  text-decoration: underline;
}
</style>

