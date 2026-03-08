<template>
  <div class="user-select-view h-full flex flex-col">
    <!-- 헤더 -->
    <div class="header bg-gradient-to-r from-primary to-primary-light text-white p-4 shadow-md">
      <div class="flex items-center gap-3">
        <el-button 
          :icon="ArrowLeft" 
          circle 
          @click="$router.push('/main')"
          class="bg-white/20 hover:bg-white/30 border-0"
        />
        <h2 class="font-semibold flex-1">사용자 선택</h2>
      </div>
    </div>

    <!-- 검색 -->
    <div class="p-3 border-b border-gray-200">
      <el-input
        v-model="searchQuery"
        placeholder="사용자 검색..."
        :prefix-icon="Search"
        clearable
      />
    </div>

    <!-- 사용자 목록 -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="filteredUsers.length === 0" class="p-4 text-center text-gray-500">
        사용자가 없습니다.
      </div>
      <UserItem
        v-for="user in filteredUsers"
        :key="user.id"
        :user="user"
        @click="selectUser(user)"
      />
    </div>

    <!-- 모드 선택 다이얼로그 -->
    <ModeSelectDialog
      v-model="showModeDialog"
      :user="selectedUser"
      @chat="openChat"
      @notification="openNotification"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Search } from '@element-plus/icons-vue'
import { watchUsers } from '@/services/userService'
import { useUserStore } from '@/stores/userStore'
import UserItem from '@/components/user/UserItem.vue'
import ModeSelectDialog from '@/components/common/ModeSelectDialog.vue'

const router = useRouter()
const userStore = useUserStore()
const users = ref([])
const searchQuery = ref('')
const showModeDialog = ref(false)
const selectedUser = ref(null)

const loadUsers = () => {
  const currentUserId = userStore.user?.id
  watchUsers((userList) => {
    users.value = userList.filter(u => u.id !== 'admin')
  }, currentUserId)
}

const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value
  const query = searchQuery.value.toLowerCase()
  return users.value.filter(user => 
    user.name?.toLowerCase().includes(query)
  )
})

const selectUser = (user) => {
  selectedUser.value = user
  showModeDialog.value = true
}

const openChat = (user) => {
  router.push(`/chat/${user.id}`)
}

const openNotification = (user) => {
  // 알림 전송 다이얼로그는 추후 구현
  console.log('알림 전송:', user)
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.header {
  background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
}
</style>

