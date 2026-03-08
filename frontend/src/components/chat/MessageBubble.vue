<template>
  <div class="message-bubble-wrapper">
    <!-- 날짜 표시 -->
    <div v-if="showDate" class="text-center text-xs text-gray-400 mb-2">
      {{ formatDate(message.time) }}
    </div>
    
    <div 
      class="message-bubble flex"
      :class="message.isSent ? 'justify-end' : 'justify-start'"
    >
      <div 
        class="px-4 py-2.5 rounded-2xl max-w-[75%]"
        :class="message.isSent 
          ? 'bg-blue-500 text-white' 
          : 'bg-white text-gray-600 border border-gray-200'"
      >
        <div v-if="message.type !== 'message'" class="flex items-center gap-2 mb-1">
          <el-icon v-if="message.type === 'meeting'" class="text-sm">
            <Calendar />
          </el-icon>
          <el-icon v-else-if="message.type === 'mail'" class="text-sm">
            <Message />
          </el-icon>
          <span class="text-xs font-semibold">
            {{ getTypeLabel(message.type) }}
          </span>
        </div>
        <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ message.text }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Calendar, Message } from '@element-plus/icons-vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  },
  showDate: {
    type: Boolean,
    default: false
  }
})

const getTypeLabel = (type) => {
  const labels = {
    meeting: '회의 요청',
    mail: '메일 확인 요청',
    message: '쪽지'
  }
  return labels[type] || '메시지'
}

const formatDate = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  
  if (messageDate.getTime() === today.getTime()) {
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `Today ${hours}:${minutes}`
  }
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric'
  }) + ` ${hours}:${minutes}`
}
</script>

