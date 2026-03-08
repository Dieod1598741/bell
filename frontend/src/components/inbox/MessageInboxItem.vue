<template>
  <div 
    class="inbox-item p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors relative group"
    :class="{ 'bg-blue-50': !item.read }"
    @click="$emit('click')"
  >
    <!-- 시간 (오른쪽 상단) -->
    <div class="absolute right-4 top-4 text-xs text-gray-500 z-10">
      {{ formatTime(item.time) }}
    </div>
    
    <!-- 삭제 텍스트 (호버 시 오른쪽 하단에 표시) -->
    <button
      class="absolute right-4 bottom-4 text-xs text-red-500 hover:text-red-700 opacity-0 group-hover:opacity-100 transition-opacity z-10"
      @click.stop="$emit('delete', item.id)"
    >
      삭제
    </button>
    
    <div class="flex items-start gap-3 pr-16">
      <!-- 아이콘 -->
      <div 
        class="w-10 h-10 rounded-full flex items-center justify-center text-white flex-shrink-0 self-center"
        :class="{
          'bg-blue-400': item.type === 'meeting',
          'bg-green-400': item.type === 'mail',
          'bg-pink-400': item.type === 'message' || item.type === 'note'
        }"
      >
        <el-icon v-if="item.type === 'meeting'" class="text-lg">
          <Calendar />
        </el-icon>
        <el-icon v-else-if="item.type === 'mail'" class="text-lg">
          <Message />
        </el-icon>
        <el-icon v-else class="text-lg">
          <ChatDotRound />
        </el-icon>
      </div>
      
      <!-- 정보 -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center mb-1">
          <h3 class="font-semibold text-gray-900">{{ item.senderName }}</h3>
        </div>
        <p class="text-xs text-gray-400 line-clamp-1">{{ item.message }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Calendar, Message, ChatDotRound } from '@element-plus/icons-vue'

const props = defineProps({
  item: {
    type: Object,
    required: true
  }
})

defineEmits(['click', 'delete'])

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

