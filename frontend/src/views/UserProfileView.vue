<template>
  <div class="user-profile-view h-full flex flex-col relative">
    <!-- 전체 배경 이미지 -->
    <div class="background-image" :style="{ backgroundImage: `url(${headerBg})` }"></div>
    
    <!-- 헤더 -->
    <div class="header-section relative z-10">
      <div class="header-content px-4 relative">
        <!-- 뒤로가기 버튼 -->
        <div class="absolute top-4 left-4">
          <el-button 
            :icon="ArrowLeft" 
            circle 
            @click="handleBack"
            class="back-button"
          />
        </div>
        
        <!-- 이름/이메일과 프로필 사진 -->
        <div class="flex items-end gap-4 px-4" style="padding-top: 100px;">
          <!-- 이름과 이메일 (세로 배치) -->
          <div class="flex-1">
            <div class="mb-1">
              <h2 class="text-3xl font-bold text-gray-900">{{ userName }}</h2>
            </div>
            <div class="flex items-center gap-2">
              <p class="text-sm text-gray-500">{{ userEmail }}</p>
              <el-icon 
                class="text-gray-500 cursor-pointer hover:text-gray-700 text-sm"
                @click="copyEmail"
                :title="'이메일 복사'"
              >
                <Edit />
              </el-icon>
            </div>
          </div>
          
          <!-- 프로필 사진 -->
          <UserAvatar
            :user="user"
            size="20"
            shadow
          />
        </div>
      </div>
    </div>

    <!-- 통계 섹션 (높이 유지용 빈 공간) -->
    <div class="px-4 py-6 border-b border-gray-100/50 relative z-10">
      <div class="flex justify-around">
        <div class="text-center">
          <div class="text-3xl font-bold text-transparent mb-1">64</div>
          <div class="text-sm text-transparent">Intimacy</div>
        </div>
        <div class="text-center">
          <div class="text-3xl font-bold text-transparent mb-1">12</div>
          <div class="text-sm text-transparent">Common</div>
        </div>
        <div class="text-center">
          <div class="text-3xl font-bold text-transparent mb-1">96</div>
          <div class="text-sm text-transparent">Interact</div>
        </div>
      </div>
    </div>

    <!-- Display 토글 (높이 유지용 빈 공간) -->
    <div class="px-4 py-4 border-b border-gray-100/50 relative z-10">
      <div class="flex items-center justify-between">
        <div>
          <div class="font-bold text-transparent mb-1">Display</div>
          <div class="text-sm text-transparent">Show us our relationship</div>
        </div>
        <div class="w-12"></div>
      </div>
    </div>

    <!-- 메뉴 옵션 -->
    <div class="relative z-10">
      <div 
        class="menu-item py-4 border-b border-gray-100/50 cursor-pointer hover:bg-white/20 transition-colors flex items-center justify-between"
        :style="{ paddingLeft: '1rem', paddingRight: '1rem' }"
        @click="showMeetingLayer = true"
      >
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-blue-500 flex items-center justify-center flex-shrink-0">
            <el-icon class="text-white text-lg">
              <Calendar />
            </el-icon>
          </div>
          <span class="font-medium text-gray-900">회의요청</span>
        </div>
        <el-icon class="text-gray-600">
          <ArrowRight />
        </el-icon>
      </div>
      
      <div 
        class="menu-item py-4 border-b border-gray-100/50 cursor-pointer hover:bg-white/20 transition-colors flex items-center justify-between"
        :style="{ paddingLeft: '1rem', paddingRight: '1rem' }"
        @click="showMailLayer = true"
      >
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0">
            <el-icon class="text-white text-lg">
              <Message />
            </el-icon>
          </div>
          <span class="font-medium text-gray-900">메일확인요청</span>
        </div>
        <el-icon class="text-gray-600">
          <ArrowRight />
        </el-icon>
      </div>
      
      <div 
        class="menu-item py-4 border-b border-gray-100/50 cursor-pointer hover:bg-white/20 transition-colors flex items-center justify-between"
        :style="{ paddingLeft: '1rem', paddingRight: '1rem' }"
        @click="showNoteLayer = true"
      >
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-pink-500 flex items-center justify-center flex-shrink-0">
            <el-icon class="text-white text-lg">
              <Message />
            </el-icon>
          </div>
          <span class="font-medium text-gray-900">쪽지보내기</span>
        </div>
        <el-icon class="text-gray-600">
          <ArrowRight />
        </el-icon>
      </div>
    </div>

    <!-- 하단 버튼 -->
    <div class="py-4 flex-shrink-0 relative z-10" :style="{ paddingLeft: '1rem', paddingRight: '1rem' }">
      <el-button
        type="primary"
        class="w-full send-button"
        @click="handleSendMessage"
      >
        Msgsnd
      </el-button>
    </div>

    <!-- 레이어들 -->
    <NoteLayer
      :visible="showNoteLayer"
      :user-id="userId"
      @update:visible="showNoteLayer = $event"
      @submit="handleNoteSubmit"
    />
    
    <MeetingLayer
      :visible="showMeetingLayer"
      :user-id="userId"
      @update:visible="showMeetingLayer = $event"
      @submit="handleMeetingSubmit"
    />
    
    <MailLayer
      :visible="showMailLayer"
      :user-id="userId"
      @update:visible="showMailLayer = $event"
      @submit="handleMailSubmit"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ChatDotRound, Message, Calendar, Edit, ArrowRight } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import NoteLayer from '@/components/layers/NoteLayer.vue'
import MeetingLayer from '@/components/layers/MeetingLayer.vue'
import MailLayer from '@/components/layers/MailLayer.vue'
import headerBg from '@/assets/images/header-bg.png'
import { getStatusLabel, isOffline as checkIsOffline } from '@/utils/userStatus'
import { getDisplayName } from '@/utils/userDisplay'
import UserAvatar from '@/components/common/UserAvatar.vue'

import { getUser } from '@/services/userService'
import { sendInboxMessage } from '@/services/inboxService'

const route = useRoute()
const router = useRouter()
const userId = route.params.userId
const user = ref(null)
const userName = computed(() => user.value ? getDisplayName(user.value) : '사용자')
const userEmail = ref('')
const userStatus = ref('offline')
const userStatusMessage = ref('Hope we happy everyday')
const displayToggle = ref(true)
const stats = ref({
  intimacy: 64,
  common: 12,
  interact: 96
})
const showNoteLayer = ref(false)
const showMeetingLayer = ref(false)
const showMailLayer = ref(false)

const isOffline = computed(() => {
  return checkIsOffline(userStatus.value)
})

const loadUserInfo = async () => {
  try {
    const firestoreUser = await getUser(userId)
    if (firestoreUser) {
      user.value = firestoreUser
      userEmail.value = firestoreUser.email || `${firestoreUser.id}@example.com`
      userStatus.value = firestoreUser.user_status || 'offline'
    }
  } catch (error) {
    console.error('사용자 정보 로드 실패:', error)
  }
}

const handleBack = () => {
  router.push({
    path: '/main',
    query: { selectedUserId: userId }
  })
}

const handleSendMessage = () => {
  router.push(`/chat/${userId}`)
}

const copyEmail = async () => {
  try {
    await navigator.clipboard.writeText(userEmail.value)
    ElMessage.success('이메일이 복사되었습니다')
  } catch (error) {
    // 클립보드 API가 지원되지 않는 경우 대체 방법
    const textArea = document.createElement('textarea')
    textArea.value = userEmail.value
    textArea.style.position = 'fixed'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      ElMessage.success('이메일이 복사되었습니다')
    } catch (err) {
      ElMessage.error('복사에 실패했습니다')
    }
    document.body.removeChild(textArea)
  }
}

const handleNoteSubmit = async (data) => {
  try {
    const { useUserStore } = await import('@/stores/userStore')
    const userStore = useUserStore()
    const currentUserId = userStore.user?.id
    if (currentUserId) {
      await sendInboxMessage(currentUserId, data.userId, data.message, data.type || 'message')
      ElMessage.success('쪽지가 전송되었습니다.')
    }
  } catch (error) {
    console.error('쪽지 전송 실패:', error)
    ElMessage.error('쪽지 전송에 실패했습니다.')
  }
}

const handleMeetingSubmit = async (data) => {
  try {
    const { useUserStore } = await import('@/stores/userStore')
    const userStore = useUserStore()
    const currentUserId = userStore.user?.id
    if (currentUserId) {
      await sendInboxMessage(currentUserId, data.userId, data.message, 'meeting')
      ElMessage.success('회의 요청이 전송되었습니다.')
    }
  } catch (error) {
    console.error('회의 요청 실패:', error)
    ElMessage.error('회의 요청 전송에 실패했습니다.')
  }
}

const handleMailSubmit = async (data) => {
  try {
    const { useUserStore } = await import('@/stores/userStore')
    const userStore = useUserStore()
    const currentUserId = userStore.user?.id
    if (currentUserId) {
      await sendInboxMessage(currentUserId, data.userId, data.message, 'mail')
      ElMessage.success('이메일 확인 요청이 전송되었습니다.')
    }
  } catch (error) {
    console.error('이메일 확인 요청 실패:', error)
    ElMessage.error('이메일 확인 요청 전송에 실패했습니다.')
  }
}

const handleKeyDown = (event) => {
  if (event.key === 'Escape') {
    handleBack()
  }
}

onMounted(() => {
  loadUserInfo()
  document.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.user-profile-view {
  overflow-y: auto;
  position: relative;
  min-height: 100%;
}

.background-image {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center top;
  background-repeat: no-repeat;
  z-index: 0;
}

.header-section {
  min-height: 240px;
  position: relative;
  overflow: hidden;
}

.header-content {
  min-height: 240px;
  position: relative;
}

.back-button {
  background: white;
  border: none;
  color: #666;
  width: 32px;
  height: 32px;
  min-width: 32px;
}

.back-button:hover {
  background: #f5f5f5;
  color: #333;
}

.send-button {
  height: 48px;
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
}

.send-button:hover {
  background: linear-gradient(135deg, #337ecc 0%, #5599ff 100%);
}
</style>

