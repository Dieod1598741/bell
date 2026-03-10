<template>
  <div class="user-list-view">
    <div class="px-4 py-2 border-b border-gray-100">
      <el-input
        v-model="searchQuery"
        placeholder="Search for contacts"
        :prefix-icon="Search"
        clearable
        size="small"
        class="search-input"
      />
    </div>
    
    <div ref="listContainer" class="flex-1 overflow-y-auto">
      <div v-if="filteredUsers.length === 0" class="empty-state">
        <p class="text-gray-400 text-sm">사용자가 없습니다</p>
      </div>
      <template v-else>
        <template v-for="(group, letter) in groupedUsers" :key="letter">
          <div v-if="group.length > 0" class="section-header px-4 py-0 bg-gray-50">
            <span class="text-xs font-medium text-gray-500">{{ letter }}</span>
          </div>
          <UserItem
            v-for="user in group"
            :key="user.id"
            :user="user"
            :selected="user.id === selectedUserId"
            @click="selectUser(user)"
          />
        </template>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { watchUsers } from '@/services/userService'
import { useUserStore } from '@/stores/userStore'
import UserItem from '@/components/user/UserItem.vue'

const props = defineProps({
  selectedUserId: {
    type: String,
    default: null
  }
})

const router = useRouter()
const userStore = useUserStore()
const searchQuery = ref('')
const listContainer = ref(null)
const allUsers = ref([])
let unwatchUsers = null

const filteredUsers = computed(() => {
  if (!searchQuery.value) return allUsers.value
  const query = searchQuery.value.toLowerCase()
  return allUsers.value.filter(user => {
    const displayName = (user.nickNm || user.name || '').toLowerCase()
    return displayName.includes(query) ||
           user.id?.toLowerCase().includes(query) ||
           user.email?.toLowerCase().includes(query)
  })
})

// 실시간 사용자 목록 감시
onMounted(() => {
  const currentUserId = userStore.user?.id
  unwatchUsers = watchUsers((users) => {
    console.log('[UserListView] received users:', users.length);
    allUsers.value = users
  }, currentUserId)
  
  if (props.selectedUserId) {
    scrollToSelectedUser()
  }
})

onUnmounted(() => {
  if (unwatchUsers) {
    unwatchUsers()
  }
})

const groupedUsers = computed(() => {
  const grouped = {}
  filteredUsers.value.forEach(user => {
    const displayName = user.nickNm || user.name || user.id || '?'
    const firstLetter = displayName.charAt(0).toUpperCase() || '?'
    if (!grouped[firstLetter]) {
      grouped[firstLetter] = []
    }
    grouped[firstLetter].push(user)
  })
  // 알파벳순으로 정렬
  return Object.keys(grouped).sort().reduce((acc, key) => {
    acc[key] = grouped[key]
    return acc
  }, {})
})

const selectUser = (user) => {
  router.push(`/user/${user.id}`)
}

const scrollToSelectedUser = async () => {
  if (!props.selectedUserId || !listContainer.value) return
  
  await nextTick()
  const userElement = listContainer.value.querySelector(`[data-user-id="${props.selectedUserId}"]`)
  if (userElement) {
    userElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

watch(() => props.selectedUserId, () => {
  if (props.selectedUserId) {
    scrollToSelectedUser()
  }
})

</script>

<style scoped>
.user-list-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.search-input :deep(.el-input__wrapper) {
  box-shadow: none;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 6px 12px;
  background: #f9fafb;
  min-height: 36px;
}

.search-input :deep(.el-input__wrapper:hover) {
  border-color: #d1d5db;
  background: white;
}

.search-input :deep(.el-input__wrapper.is-focus) {
  border-color: #409EFF;
  background: white;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}
</style>

