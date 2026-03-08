<template>
  <div class="main-sidebar w-16 bg-blue-500 flex flex-col items-center py-4 relative flex-shrink-0 h-full">
    <!-- 프로필 -->
    <div class="flex flex-col items-center gap-2 pt-8 mb-20">
      <UserAvatar
        :user="userStore.user"
        size="12"
        clickable
        status-clickable
        shadow
        @click="$emit('open-profile')"
        @status-click="$emit('open-status')"
      />
    </div>
    
    <!-- 메뉴 아이콘들 -->
    <div class="flex-1 flex flex-col gap-4">
      <!-- 채팅 -->
      <div 
        class="menu-item w-12 h-12 rounded-lg flex items-center justify-center cursor-pointer transition-colors"
        :class="activeMenu === 'chat' ? 'bg-white text-blue-500' : 'text-white hover:bg-blue-600'"
        @click="$emit('menu-change', 'chat')"
      >
        <el-icon class="text-2xl relative">
          <ChatDotRound />
          <span v-if="chatUnreadCount > 0" class="absolute top-0 right-0 w-5 h-5 bg-red-500 rounded-full border-2 border-blue-500 flex items-center justify-center transform translate-x-1/2 -translate-y-1/2">
            <span class="text-[10px] text-white font-bold">{{ chatUnreadCount > 9 ? '9+' : chatUnreadCount }}</span>
          </span>
        </el-icon>
      </div>
      
      <!-- 유저 -->
      <div 
        class="menu-item w-12 h-12 rounded-lg flex items-center justify-center cursor-pointer transition-colors"
        :class="activeMenu === 'users' ? 'bg-white text-blue-500' : 'text-white hover:bg-blue-600'"
        @click="$emit('menu-change', 'users')"
      >
        <el-icon class="text-2xl">
          <User />
        </el-icon>
      </div>
      
      <!-- 쪽지함 -->
      <div 
        class="menu-item w-12 h-12 rounded-lg flex items-center justify-center cursor-pointer transition-colors"
        :class="activeMenu === 'inbox' ? 'bg-white text-blue-500' : 'text-white hover:bg-blue-600'"
        @click="$emit('menu-change', 'inbox')"
      >
        <el-icon class="text-2xl relative">
          <Message />
          <span v-if="unreadCount > 0" class="absolute top-0 right-0 w-5 h-5 bg-red-500 rounded-full border-2 border-blue-500 flex items-center justify-center transform translate-x-1/2 -translate-y-1/2">
            <span class="text-[10px] text-white font-bold">{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
          </span>
        </el-icon>
      </div>
    </div>
    
    <!-- 하단 메뉴들 -->
    <div class="flex flex-col gap-4">
      <!-- 관리자 (관리자만 표시) -->
      <div 
        v-if="isAdmin"
        class="menu-item w-12 h-12 rounded-lg flex items-center justify-center cursor-pointer transition-colors text-white hover:bg-blue-600"
        @click="$router.push('/admin')"
      >
        <el-icon class="text-2xl">
          <Setting />
        </el-icon>
      </div>
      
      <!-- 햄버거 메뉴 (사이드바 토글) -->
      <div 
        class="menu-item w-12 h-12 rounded-lg flex items-center justify-center cursor-pointer text-white hover:bg-blue-600 transition-colors"
        @click="$emit('toggle-sidebar')"
      >
        <div class="hamburger-icon flex flex-col gap-1.5">
          <span class="w-5 h-0.5 bg-white rounded"></span>
          <span class="w-5 h-0.5 bg-white rounded"></span>
          <span class="w-5 h-0.5 bg-white rounded"></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotRound, User, Message, Setting } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/userStore.js'
import UserAvatar from '@/components/common/UserAvatar.vue'

const router = useRouter()

const userStore = useUserStore()

const props = defineProps({
  activeMenu: {
    type: String,
    default: 'chat'
  },
  unreadCount: {
    type: Number,
    default: 0
  },
  chatUnreadCount: {
    type: Number,
    default: 0
  }
})

defineEmits(['menu-change', 'toggle-sidebar', 'open-status', 'open-profile'])

const isAdmin = computed(() => {
  return userStore.user?.permission === 'admin'
})
</script>

<style scoped>
.main-sidebar {
  background: #409EFF;
}

.status-indicator {
  box-shadow: 0 0 0 2px #409EFF;
}
</style>

