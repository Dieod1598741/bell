<template>
  <ActionLayer :visible="visible" @update:visible="$emit('update:visible', $event)">
    <div class="profile-edit-layer">
      <h3 class="text-xl font-bold mb-6">내 정보 수정</h3>
      
      <div class="form-content">
        <!-- 프로필 이미지 -->
        <div class="form-group-image">
          <div class="flex justify-center items-center gap-4">
            <div class="relative">
              <div 
                ref="profileImageButtonRef"
                class="w-24 h-24 rounded-full flex items-center justify-center text-white font-bold text-3xl shadow-md overflow-hidden cursor-pointer hover:opacity-80 transition-opacity"
                :style="{ backgroundColor: profileColor }"
                @click="showImageSelector = true"
              >
                <img 
                  v-if="profileImage" 
                  :src="profileImage" 
                  alt="Profile" 
                  class="w-full h-full object-contain"
                  style="padding: 15%"
                />
                <span v-else>{{ userName?.charAt(0).toUpperCase() || '?' }}</span>
              </div>
            </div>
            <div class="color-picker-wrapper">
              <div class="color-label">배경 색상</div>
              <el-color-picker
                v-model="profileColor"
                :predefine="predefineColors"
                show-alpha
                color-format="hex"
                size="default"
              />
            </div>
          </div>
        </div>

        <!-- 아이디 -->
        <div class="form-group-with-label">
          <span class="input-label-top">아이디</span>
          <el-input
            v-model="userId"
            placeholder="아이디를 입력하세요"
            disabled
          />
        </div>

        <!-- 이름 -->
        <div class="form-group-with-label">
          <span class="input-label-top">이름</span>
          <el-input
            v-model="name"
            placeholder="이름을 입력하세요"
          />
        </div>

        <!-- 닉네임 -->
        <div class="form-group-with-label">
          <span class="input-label-top">닉네임</span>
          <el-input
            v-model="nickNm"
            placeholder="닉네임을 입력하세요"
          />
        </div>

        <!-- 이메일 -->
        <div class="form-group-with-label">
          <span class="input-label-top">이메일</span>
          <el-input
            v-model="email"
            type="email"
            placeholder="이메일을 입력하세요"
          />
        </div>

        <!-- 비밀번호 변경 (선택사항) -->
        <div class="form-group-with-label">
          <span class="input-label-top">비밀번호 변경 <span class="optional-label">(선택)</span></span>
          <el-input
            v-model="newPassword"
            type="password"
            placeholder="변경할 비밀번호를 입력하세요 (선택사항)"
            show-password
          />
        </div>

        <div v-if="newPassword" class="form-group-with-label">
          <span class="input-label-top">비밀번호 확인</span>
          <el-input
            v-model="confirmPassword"
            type="password"
            placeholder="비밀번호를 다시 입력하세요"
            show-password
          />
        </div>

        <!-- 저장 버튼 -->
        <el-button 
          type="primary" 
          class="w-full submit-button" 
          @click="handleSave"
          :disabled="!name.trim() || !nickNm.trim() || !email.trim()"
        >
          저장
        </el-button>
      </div>
    </div>
    
    <!-- 프로필 이미지 선택 다이얼로그 -->
    <ProfileImageSelector
      v-model="showImageSelector"
      :current-image="profileImage"
      :trigger-element="profileImageButtonRef"
      @select="handleImageSelect"
    />
  </ActionLayer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useUserStore } from '@/stores/userStore'
import ActionLayer from '@/components/layers/ActionLayer.vue'
import ProfileImageSelector from '@/components/common/ProfileImageSelector.vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible'])

const userStore = useUserStore()
const userId = ref('')
const name = ref('')
const nickNm = ref('')
const email = ref('')
const profileImage = ref('')
const profileColor = ref('#409EFF')
const newPassword = ref('')
const confirmPassword = ref('')
const showImageSelector = ref(false)
const profileImageButtonRef = ref(null)

const userName = computed(() => userStore.user?.name || '사용자')

// 미리 정의된 색상 목록 (Element Plus color-picker용)
const predefineColors = [
  '#409EFF', // 파란색
  '#67C23A', // 초록색
  '#E6A23C', // 주황색
  '#F56C6C', // 빨간색
  '#F78989', // 핑크색
  '#50C878', // 청록색
  '#F7BA2A', // 노란색
  '#A0522D', // 갈색
  '#909399', // 회색
  '#303133', // 검은색
  '#87CEEB', // 하늘색
  '#9C27B0'  // 보라색
]

watch(() => props.visible, async (newVal) => {
  if (newVal && userStore.user) {
    // Firestore에서 최신 사용자 정보 가져오기
    try {
      const { getUser } = await import('@/services/userService')
      const latestUser = await getUser(userStore.user.id)
      
      if (latestUser) {
        // Firestore에서 가져온 최신 정보 사용
        userId.value = latestUser.id || ''
        name.value = latestUser.name || ''
        nickNm.value = latestUser.nickNm || ''
        email.value = latestUser.email || ''
        profileImage.value = latestUser.avatar || '/icon/icon1.svg'
        profileColor.value = latestUser.avatar_color || '#409EFF'
      } else {
        // Firestore에서 가져오지 못하면 userStore의 정보 사용
        userId.value = userStore.user.id || ''
        name.value = userStore.user.name || ''
        nickNm.value = userStore.user.nickNm || ''
        email.value = userStore.user.email || ''
        profileImage.value = userStore.user.avatar || '/icon/icon1.svg'
        profileColor.value = userStore.user.avatar_color || '#409EFF'
      }
    } catch (e) {
      console.error('[ProfileEditLayer] 사용자 정보 로드 실패:', e)
      // 에러 발생 시 userStore의 정보 사용
      userId.value = userStore.user.id || ''
      name.value = userStore.user.name || ''
      nickNm.value = userStore.user.nickNm || ''
      email.value = userStore.user.email || ''
      profileImage.value = userStore.user.avatar || '/icon/icon1.svg'
      profileColor.value = userStore.user.avatar_color || '#409EFF'
    }
    
    newPassword.value = ''
    confirmPassword.value = ''
  }
})

const handleImageSelect = (iconPath) => {
  profileImage.value = iconPath
}

const handleSave = async () => {
  if (!name.value.trim() || !nickNm.value.trim() || !email.value.trim()) {
    ElMessage.warning('이름, 닉네임, 이메일을 모두 입력해주세요')
    return
  }

  // 비밀번호 변경 확인
  if (newPassword.value || confirmPassword.value) {
    if (newPassword.value !== confirmPassword.value) {
      ElMessage.error('비밀번호가 일치하지 않습니다')
      return
    }
    if (newPassword.value.length < 6) {
      ElMessage.error('비밀번호는 6자 이상이어야 합니다')
      return
    }
  }

  const updatedUser = {
    id: userStore.user.id, // ID는 명시적으로 전달
    name: name.value.trim(),
    nickNm: nickNm.value.trim(),
    email: email.value.trim(),
    avatar: profileImage.value,
    avatar_color: profileColor.value
  }

  // 비밀번호가 입력된 경우에만 업데이트
  if (newPassword.value && newPassword.value === confirmPassword.value) {
    updatedUser.password = newPassword.value
  }

  console.log('[ProfileEditLayer] 업데이트할 데이터:', updatedUser)
  const result = await userStore.updateUser(updatedUser)
  
  if (result && result.success) {
    ElMessage.success('정보가 저장되었습니다')
    emit('update:visible', false)
  } else {
    ElMessage.error(result?.error || '정보 저장에 실패했습니다')
  }
}
</script>

<style scoped>
.profile-edit-layer {
  padding: 0;
}

.form-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group-image {
  display: flex;
  justify-content: center;
  margin-bottom: 8px;
}

.color-picker-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.color-label {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
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

.optional-label {
  font-size: 10px;
  color: #9ca3af;
  font-weight: 400;
}

:deep(.el-input__wrapper) {
  border-radius: 12px;
  padding: 8px 16px;
  min-height: 40px;
}

.submit-button {
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  border-radius: 12px;
  padding: 8px 16px;
  min-height: 40px;
}
</style>

