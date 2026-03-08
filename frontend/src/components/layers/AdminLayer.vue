<template>
  <ActionLayer :visible="visible" @update:visible="$emit('update:visible', $event)">
    <div class="admin-layer">
      <h3 class="text-xl font-bold mb-6">관리자</h3>
      
      <!-- 탭 -->
      <div class="tabs mb-4">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          class="tab-button"
          :class="{ active: activeTab === tab.value }"
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- 승인 대기 사용자 -->
      <div v-if="activeTab === 'pending'" class="tab-content">
        <div v-if="pendingUsers.length === 0" class="empty-state">
          <p class="text-gray-400 text-sm">승인 대기 사용자가 없습니다</p>
        </div>
        <div v-else class="pending-user-list">
          <div
            v-for="user in pendingUsers"
            :key="user.id"
            class="pending-user-item"
          >
            <div class="pending-user-info">
              <div class="pending-user-header">
                <div class="pending-user-name">{{ user.nickNm || user.name }}</div>
                <div class="pending-user-badge">승인 대기</div>
              </div>
              <div class="pending-user-details">
                <div class="pending-user-detail-item">
                  <span class="detail-label">ID:</span>
                  <span class="detail-value">{{ user.id }}</span>
                </div>
                <div class="pending-user-detail-item">
                  <span class="detail-label">이메일:</span>
                  <span class="detail-value">{{ user.email }}</span>
                </div>
              </div>
            </div>
            <div class="pending-user-actions">
              <el-button
                type="success"
                size="small"
                @click="approveUser(user.id)"
                :loading="loadingUsers[user.id]"
                class="action-button"
              >
                승인
              </el-button>
              <el-button
                type="danger"
                size="small"
                @click="rejectUser(user.id)"
                :loading="loadingUsers[user.id]"
                class="action-button"
              >
                거절
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 사용자 추가 -->
      <div v-if="activeTab === 'add'" class="tab-content">
        <div class="form-content">
          <div class="form-group-with-label">
            <span class="input-label-top">아이디</span>
            <el-input
              v-model="addForm.userId"
              placeholder="아이디를 입력하세요"
            />
          </div>

          <div class="form-group-with-label">
            <span class="input-label-top">이름</span>
            <el-input
              v-model="addForm.name"
              placeholder="이름을 입력하세요"
            />
          </div>

          <div class="form-group-with-label">
            <span class="input-label-top">닉네임</span>
            <el-input
              v-model="addForm.nickNm"
              placeholder="닉네임을 입력하세요"
            />
          </div>

          <div class="form-group-with-label">
            <span class="input-label-top">이메일</span>
            <el-input
              v-model="addForm.email"
              type="email"
              placeholder="이메일을 입력하세요"
            />
          </div>

          <div class="form-group-with-label">
            <span class="input-label-top">비밀번호</span>
            <el-input
              v-model="addForm.password"
              type="password"
              placeholder="비밀번호를 입력하세요"
              show-password
            />
          </div>

          <div class="form-group-with-label">
            <span class="input-label-top">비밀번호 확인</span>
            <el-input
              v-model="addForm.confirmPassword"
              type="password"
              placeholder="비밀번호를 다시 입력하세요"
              show-password
            />
          </div>

          <div class="form-group-with-label">
            <span class="input-label-top">권한</span>
            <el-select v-model="addForm.permission" class="w-full">
              <el-option label="승인됨" value="approved" />
              <el-option label="관리자" value="admin" />
            </el-select>
          </div>

          <div v-if="addError" class="error-message text-red-500 text-sm">
            {{ addError }}
          </div>

          <el-button
            type="primary"
            class="w-full submit-button"
            @click="handleAddUser"
            :loading="addingUser"
            :disabled="!isAddFormValid"
          >
            사용자 추가
          </el-button>
        </div>
      </div>

      <!-- 사용자 관리 -->
      <div v-if="activeTab === 'manage'" class="tab-content">
        <div class="search-box mb-4">
          <el-input
            v-model="searchQuery"
            placeholder="사용자 검색 (이름, ID, 이메일)"
            clearable
            size="small"
          />
        </div>
        
        <div v-if="filteredUsers.length === 0" class="empty-state">
          <p class="text-gray-400 text-sm">사용자가 없습니다</p>
        </div>
        <div v-else class="manage-user-list">
          <div
            v-for="user in filteredUsers"
            :key="user.id"
            class="manage-user-item"
          >
            <div class="manage-user-info">
              <div class="manage-user-header">
                <div class="manage-user-name">{{ user.nickNm || user.name }}</div>
                <span v-if="user.permission === 'admin'" class="manage-user-permission" :class="getPermissionClass(user.permission)">
                  {{ getPermissionLabel(user.permission) }}
                </span>
              </div>
              <div class="manage-user-details">
                <div class="manage-user-detail-row">
                  <span class="detail-label">ID:</span>
                  <span class="detail-value">{{ user.id }}</span>
                </div>
                <div class="manage-user-detail-row">
                  <span class="detail-label">이메일:</span>
                  <span class="detail-value">{{ user.email }}</span>
                </div>
              </div>
            </div>
            <div class="manage-user-actions">
              <el-select
                v-model="user.permission"
                size="small"
                @change="updatePermission(user.id, user.permission)"
                class="permission-select"
              >
                <el-option label="승인 대기" value="pending" />
                <el-option label="승인됨" value="approved" />
                <el-option label="거부됨" value="rejected" />
                <el-option label="관리자" value="admin" />
              </el-select>
            </div>
          </div>
        </div>
      </div>

      <!-- 알람 발송 -->
      <div v-if="activeTab === 'announcement'" class="tab-content">
        <div class="form-content">
          <div class="form-group-with-label">
            <span class="input-label-top">알람 메시지</span>
            <el-input
              v-model="announcementMessage"
              type="textarea"
              :rows="4"
              placeholder="알람 메시지를 입력하세요"
              maxlength="500"
              show-word-limit
            />
          </div>

          <div class="form-group-with-label">
            <div class="flex items-center justify-between mb-2">
              <span class="input-label-top">수신자 선택</span>
              <div class="flex items-center gap-2">
                <el-checkbox
                  v-model="selectAllUsers"
                  @change="handleSelectAll"
                >
                  전체 선택
                </el-checkbox>
              </div>
            </div>
            <div class="announcement-user-list border border-gray-200 rounded-lg p-3 max-h-64 overflow-y-auto">
              <div v-if="filteredUsers.length === 0" class="empty-state py-8">
                <p class="text-gray-400 text-sm">사용자가 없습니다</p>
              </div>
              <div
                v-for="user in filteredUsers"
                :key="user.id"
                class="announcement-user-item flex items-center gap-3 p-2 hover:bg-gray-50 rounded cursor-pointer"
                @click="toggleUserSelection(user.id)"
              >
                <el-checkbox
                  :model-value="selectedUsers.has(user.id)"
                  @change="toggleUserSelection(user.id)"
                  @click.stop
                />
                <div class="flex-1 min-w-0">
                  <div class="font-medium text-sm text-gray-900">
                    {{ user.nickNm || user.name }}
                  </div>
                  <div class="text-xs text-gray-500">{{ user.id }}</div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="announcementError" class="error-message text-red-500 text-sm">
            {{ announcementError }}
          </div>

          <el-button
            type="primary"
            class="w-full submit-button"
            @click="handleSendAnnouncement"
            :loading="sendingAnnouncement"
            :disabled="!isAnnouncementFormValid"
          >
            알람 발송 ({{ selectedUsers.size }}명)
          </el-button>
        </div>
      </div>
    </div>
  </ActionLayer>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { loadPendingUsers, updateUserPermission, addUserByAdmin, watchAllUsers } from '@/services/userService'
import { sendAnnouncement } from '@/services/announcementService'
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

const activeTab = ref('pending')
const tabs = [
  { value: 'pending', label: '승인 대기' },
  { value: 'add', label: '사용자 추가' },
  { value: 'manage', label: '사용자 관리' },
  { value: 'announcement', label: '알람 발송' }
]

const pendingUsers = ref([])
const allUsers = ref([])
const searchQuery = ref('')
const loadingUsers = ref({})
const addingUser = ref(false)
const addError = ref('')

const addForm = ref({
  userId: '',
  name: '',
  nickNm: '',
  email: '',
  password: '',
  confirmPassword: '',
  permission: 'approved'
})

// 알람 발송 관련
const selectedUsers = ref(new Set())
const selectAllUsers = ref(false)
const announcementMessage = ref('')
const sendingAnnouncement = ref(false)
const announcementError = ref('')

const isAddFormValid = computed(() => {
  return addForm.value.userId.trim() &&
         addForm.value.name.trim() &&
         addForm.value.nickNm.trim() &&
         addForm.value.email.trim() &&
         addForm.value.password.trim() &&
         addForm.value.password === addForm.value.confirmPassword &&
         addForm.value.password.length >= 6
})

const isAnnouncementFormValid = computed(() => {
  return announcementMessage.value.trim() && selectedUsers.value.size > 0
})

const filteredUsers = computed(() => {
  if (!searchQuery.value) return allUsers.value
  const query = searchQuery.value.toLowerCase()
  return allUsers.value.filter(user =>
        (user.nickNm || user.name)?.toLowerCase().includes(query) ||
    user.id?.toLowerCase().includes(query) ||
    user.email?.toLowerCase().includes(query)
  )
})

const getPermissionLabel = (permission) => {
  const labels = {
    pending: '승인 대기',
    approved: '승인됨',
    rejected: '거부됨',
    admin: '관리자'
  }
  return labels[permission] || permission
}

const getPermissionClass = (permission) => {
  return {
    'permission-pending': permission === 'pending',
    'permission-approved': permission === 'approved',
    'permission-rejected': permission === 'rejected',
    'permission-admin': permission === 'admin'
  }
}

const loadPendingUsersList = async () => {
  try {
    const result = await loadPendingUsers(100) // 모든 승인 대기 사용자
    pendingUsers.value = result.users
  } catch (error) {
    console.error('승인 대기 사용자 로드 실패:', error)
  }
}

const approveUser = async (userId) => {
  loadingUsers.value[userId] = true
  try {
    const result = await updateUserPermission(userId, 'approved')
    if (result.success) {
      await loadPendingUsersList()
      await loadAllUsers()
    }
  } catch (error) {
    console.error('사용자 승인 실패:', error)
  } finally {
    loadingUsers.value[userId] = false
  }
}

const rejectUser = async (userId) => {
  loadingUsers.value[userId] = true
  try {
    const result = await updateUserPermission(userId, 'rejected')
    if (result.success) {
      await loadPendingUsersList()
      await loadAllUsers()
    }
  } catch (error) {
    console.error('사용자 거부 실패:', error)
  } finally {
    loadingUsers.value[userId] = false
  }
}

const updatePermission = async (userId, permission) => {
  try {
    const result = await updateUserPermission(userId, permission)
    if (result.success) {
      await loadAllUsers()
      if (activeTab.value === 'pending') {
        await loadPendingUsersList()
      }
    }
  } catch (error) {
    console.error('권한 변경 실패:', error)
  }
}

const handleAddUser = async () => {
  if (!addForm.value.userId.trim() || !addForm.value.name.trim() || !addForm.value.nickNm.trim() || !addForm.value.email.trim()) {
    addError.value = '모든 필드를 입력해주세요.'
    return
  }

  if (!addForm.value.password.trim()) {
    addError.value = '비밀번호를 입력해주세요.'
    return
  }

  if (addForm.value.password.length < 6) {
    addError.value = '비밀번호는 6자 이상이어야 합니다.'
    return
  }

  if (addForm.value.password !== addForm.value.confirmPassword) {
    addError.value = '비밀번호가 일치하지 않습니다.'
    return
  }

  addingUser.value = true
  addError.value = ''

  try {
    const result = await addUserByAdmin({
      id: addForm.value.userId.trim(),
      name: addForm.value.name.trim(),
      nickNm: addForm.value.nickNm.trim(),
      email: addForm.value.email.trim(),
      password: addForm.value.password.trim(),
      permission: addForm.value.permission,
      del_yn: 'n',
      connection_status: 'offline',
      user_status: 'offline'
    })

    if (result.success) {
      addForm.value = {
        userId: '',
        name: '',
        nickNm: '',
        email: '',
        password: '',
        confirmPassword: '',
        permission: 'approved'
      }
      await loadAllUsers()
      if (activeTab.value === 'pending') {
        await loadPendingUsersList()
      }
    } else {
      addError.value = result.error || '사용자 추가에 실패했습니다.'
    }
  } catch (error) {
    console.error('사용자 추가 오류:', error)
    addError.value = '사용자 추가 중 오류가 발생했습니다.'
  } finally {
    addingUser.value = false
  }
}

let unwatchUsers = null

const loadAllUsers = () => {
  // 모든 사용자 목록 실시간 감시 (관리자용)
  if (unwatchUsers) {
    unwatchUsers() // 기존 리스너 제거
  }
  
  unwatchUsers = watchAllUsers((users) => {
    allUsers.value = users
  })
}

watch(() => props.visible, (newVal) => {
  if (newVal) {
    loadPendingUsersList()
    loadAllUsers()
  }
})

onMounted(() => {
  if (props.visible) {
    loadPendingUsersList()
    loadAllUsers()
  }
})

const handleSelectAll = (checked) => {
  if (checked) {
    filteredUsers.value.forEach(user => {
      selectedUsers.value.add(user.id)
    })
  } else {
    selectedUsers.value.clear()
  }
}

const toggleUserSelection = (userId) => {
  if (selectedUsers.value.has(userId)) {
    selectedUsers.value.delete(userId)
  } else {
    selectedUsers.value.add(userId)
  }
  // 전체 선택 상태 업데이트
  selectAllUsers.value = filteredUsers.value.length > 0 && 
    filteredUsers.value.every(user => selectedUsers.value.has(user.id))
}

watch(() => filteredUsers.value, () => {
  // 필터된 사용자 목록이 변경되면 전체 선택 상태 업데이트
  selectAllUsers.value = filteredUsers.value.length > 0 && 
    filteredUsers.value.every(user => selectedUsers.value.has(user.id))
}, { deep: true })

const handleSendAnnouncement = async () => {
  if (!announcementMessage.value.trim()) {
    announcementError.value = '알람 메시지를 입력해주세요.'
    return
  }

  if (selectedUsers.value.size === 0) {
    announcementError.value = '최소 1명 이상의 수신자를 선택해주세요.'
    return
  }

  sendingAnnouncement.value = true
  announcementError.value = ''

  try {
    const userIds = Array.from(selectedUsers.value)
    const result = await sendAnnouncement(
      userIds,
      announcementMessage.value.trim(),
      userStore.user?.id || 'admin'
    )

    if (result.success) {
      // 성공 시 폼 초기화
      announcementMessage.value = ''
      selectedUsers.value.clear()
      selectAllUsers.value = false
      announcementError.value = ''
    } else {
      announcementError.value = result.error || '알람 발송에 실패했습니다.'
    }
  } catch (error) {
    console.error('알람 발송 오류:', error)
    announcementError.value = '알람 발송 중 오류가 발생했습니다.'
  } finally {
    sendingAnnouncement.value = false
  }
}

onUnmounted(() => {
  if (unwatchUsers) {
    unwatchUsers()
  }
})
</script>

<style scoped>
.admin-layer {
  padding: 20px 0;
  max-height: 80vh;
  overflow-y: auto;
}

.tabs {
  display: flex;
  gap: 8px;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 8px;
}

.tab-button {
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.tab-button:hover {
  background: #f3f4f6;
  color: #374151;
}

.tab-button.active {
  color: #409EFF;
  background: #ecf5ff;
}

.tab-content {
  margin-top: 16px;
}

/* 승인 대기 사용자 리스트 */
.pending-user-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pending-user-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: white;
  transition: all 0.2s;
}

.pending-user-item:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.pending-user-info {
  flex: 1;
  min-width: 0;
}

.pending-user-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.pending-user-name {
  font-weight: 600;
  font-size: 15px;
  color: #111827;
}

.pending-user-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  background: #fef3c7;
  color: #92400e;
}

.pending-user-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pending-user-detail-item {
  display: flex;
  gap: 8px;
  font-size: 13px;
}

.detail-label {
  color: #6b7280;
  font-weight: 500;
  min-width: 50px;
}

.detail-value {
  color: #374151;
  word-break: break-all;
}

.pending-user-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  margin-left: 16px;
}

.action-button {
  min-width: 70px;
}

/* 사용자 관리 리스트 */
.manage-user-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.manage-user-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: white;
  transition: all 0.2s;
  min-width: 0;
}

.manage-user-item:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.manage-user-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.manage-user-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.manage-user-name {
  font-weight: 600;
  font-size: 15px;
  color: #111827;
}

.manage-user-permission {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}

.permission-pending {
  background: #fef3c7;
  color: #92400e;
}

.permission-approved {
  background: #d1fae5;
  color: #065f46;
}

.permission-rejected {
  background: #fee2e2;
  color: #991b1b;
}

.permission-admin {
  background: #dbeafe;
  color: #1e40af;
}

.manage-user-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.manage-user-detail-row {
  display: flex;
  gap: 8px;
  font-size: 13px;
  flex-wrap: wrap;
}

.manage-user-actions {
  display: flex;
  flex-shrink: 0;
  margin-left: 16px;
}

.permission-select {
  min-width: 130px;
  width: 130px;
}

.form-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group-with-label {
  position: relative;
}

.input-label-top {
  position: absolute;
  top: -8px;
  left: 12px;
  font-size: 11px;
  font-weight: 500;
  color: #6b7280;
  padding: 0 4px;
  z-index: 1;
  background: white;
}

.submit-button {
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.search-box {
  margin-bottom: 16px;
}

/* 알람 발송 */
.announcement-user-list {
  background: #f9fafb;
}

.announcement-user-item {
  transition: background 0.2s;
}

.announcement-user-item:hover {
  background: #f3f4f6;
}
</style>

