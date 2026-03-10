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
      <!-- 로딩 스켈레톤 -->
      <div v-if="isLoading" class="skeleton-list">
        <div v-for="i in 6" :key="i" class="skeleton-item">
          <div class="skeleton-avatar"></div>
          <div class="skeleton-content">
            <div class="skeleton-line wide"></div>
            <div class="skeleton-line narrow"></div>
          </div>
        </div>
      </div>
      <div v-else-if="filteredUsers.length === 0" class="empty-state">
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
  },
  searchQuery: {
    type: String,
    default: ''
  }
})

const router = useRouter()
const userStore = useUserStore()
const searchQuery = ref('')
const listContainer = ref(null)
const allUsers = ref([])
const isLoading = ref(true)
let unwatchUsers = null

// MainView에서 prop으로 받은 searchQuery를 내부 ref에 동기화
watch(() => props.searchQuery, (val) => {
  searchQuery.value = val
}, { immediate: true })

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
    isLoading.value = false
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

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

/* 스켈레톤 */
.skeleton-list { padding: 8px 0; }
.skeleton-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; }
.skeleton-avatar { width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(90deg,#f0f0f0 25%,#e0e0e0 50%,#f0f0f0 75%); background-size: 200% 100%; animation: shimmer 1.2s infinite; flex-shrink: 0; }
.skeleton-content { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.skeleton-line { height: 11px; border-radius: 6px; background: linear-gradient(90deg,#f0f0f0 25%,#e0e0e0 50%,#f0f0f0 75%); background-size: 200% 100%; animation: shimmer 1.2s infinite; }
.skeleton-line.wide { width: 65%; }
.skeleton-line.narrow { width: 40%; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

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

