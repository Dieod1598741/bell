<template>
  <ActionLayer :visible="visible" @update:visible="$emit('update:visible', $event)">
    <div class="signup-layer">
      <h3 class="text-xl font-bold mb-6">회원가입</h3>
      
      <div class="form-content">
        <div class="form-group-with-label">
          <span class="input-label-top">아이디</span>
          <el-input
            v-model="form.userId"
            placeholder="아이디를 입력하세요"
            :disabled="loading"
            @blur="checkUserId"
          />
          <div v-if="userIdError" class="error-text text-xs text-red-500 mt-1">
            {{ userIdError }}
          </div>
          <div v-else-if="userIdChecked && !userIdError" class="success-text text-xs text-green-500 mt-1">
            사용 가능한 아이디입니다
          </div>
        </div>

        <div class="form-group-with-label">
          <span class="input-label-top">이름</span>
          <el-input
            v-model="form.name"
            placeholder="이름을 입력하세요"
            :disabled="loading"
          />
        </div>

        <div class="form-group-with-label">
          <span class="input-label-top">닉네임</span>
          <el-input
            v-model="form.nickNm"
            placeholder="닉네임을 입력하세요"
            :disabled="loading"
            @blur="checkNickname"
          />
          <div v-if="nicknameError" class="error-text text-xs text-red-500 mt-1">
            {{ nicknameError }}
          </div>
          <div v-else-if="nicknameChecked && !nicknameError" class="success-text text-xs text-green-500 mt-1">
            사용 가능한 닉네임입니다
          </div>
        </div>

        <div class="form-group-with-label">
          <span class="input-label-top">이메일</span>
          <el-input
            v-model="form.email"
            type="email"
            placeholder="이메일을 입력하세요"
            :disabled="loading"
          />
        </div>

        <div class="form-group-with-label">
          <span class="input-label-top">비밀번호</span>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="비밀번호를 입력하세요"
            show-password
            :disabled="loading"
          />
          <div class="password-hint text-xs text-gray-500 mt-1">
            영문, 숫자, 특수문자 포함 8자 이상
          </div>
        </div>

        <div class="form-group-with-label">
          <span class="input-label-top">비밀번호 확인</span>
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="비밀번호를 다시 입력하세요"
            show-password
            :disabled="loading"
            @blur="checkPasswordMatch"
          />
          <div v-if="passwordMatchError" class="error-text text-xs text-red-500 mt-1">
            {{ passwordMatchError }}
          </div>
          <div v-else-if="form.confirmPassword && form.password === form.confirmPassword" class="success-text text-xs text-green-500 mt-1">
            비밀번호가 일치합니다
          </div>
        </div>

        <div v-if="error" class="error-message text-red-500 text-sm mb-4">
          {{ error }}
        </div>

        <el-button 
          type="primary" 
          class="w-full submit-button" 
          @click="handleSignup"
          :loading="loading"
          :disabled="!isFormValid"
        >
          회원가입
        </el-button>
      </div>
    </div>
  </ActionLayer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createUser, checkUserIdExists, checkNicknameExists, hashPassword } from '@/services/userService'
import ActionLayer from '@/components/layers/ActionLayer.vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'success'])

const form = ref({
  userId: '',
  name: '',
  nickNm: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const loading = ref(false)
const error = ref('')
const userIdError = ref('')
const nicknameError = ref('')
const passwordMatchError = ref('')
const userIdChecked = ref(false)
const nicknameChecked = ref(false)

// 비밀번호 유효성 검사
const isPasswordValid = computed(() => {
  const password = form.value.password
  if (!password) return false
  // 영문, 숫자, 특수문자 포함 8자 이상
  const hasLetter = /[a-zA-Z]/.test(password)
  const hasNumber = /[0-9]/.test(password)
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password)
  return password.length >= 8 && hasLetter && hasNumber && hasSpecial
})

const isFormValid = computed(() => {
  return form.value.userId.trim() &&
         form.value.name.trim() &&
         form.value.nickNm.trim() &&
         form.value.email.trim() &&
         form.value.password.trim() &&
         form.value.password === form.value.confirmPassword &&
         isPasswordValid.value &&
         !userIdError.value &&
         !nicknameError.value &&
         userIdChecked.value &&
         nicknameChecked.value
})

// 아이디 중복 검증
const checkUserId = async () => {
  const userId = form.value.userId.trim()
  if (!userId) {
    userIdError.value = ''
    userIdChecked.value = false
    return
  }
  
  try {
    const result = await checkUserIdExists(userId)
    if (result.exists) {
      userIdError.value = '이미 사용 중인 아이디입니다'
      userIdChecked.value = false
    } else {
      userIdError.value = ''
      userIdChecked.value = true
    }
  } catch (err) {
    console.error('아이디 중복 검증 오류:', err)
    userIdError.value = '아이디 중복 검증 중 오류가 발생했습니다'
    userIdChecked.value = false
  }
}

// 닉네임 중복 검증
const checkNickname = async () => {
  const nickname = form.value.nickNm.trim()
  if (!nickname) {
    nicknameError.value = ''
    nicknameChecked.value = false
    return
  }
  
  try {
    const result = await checkNicknameExists(nickname)
    if (result.exists) {
      nicknameError.value = '이미 사용 중인 닉네임입니다'
      nicknameChecked.value = false
    } else {
      nicknameError.value = ''
      nicknameChecked.value = true
    }
  } catch (err) {
    console.error('닉네임 중복 검증 오류:', err)
    nicknameError.value = '닉네임 중복 검증 중 오류가 발생했습니다'
    nicknameChecked.value = false
  }
}

// 비밀번호 일치 확인
const checkPasswordMatch = () => {
  if (!form.value.confirmPassword) {
    passwordMatchError.value = ''
    return
  }
  
  if (form.value.password !== form.value.confirmPassword) {
    passwordMatchError.value = '비밀번호가 일치하지 않습니다'
  } else {
    passwordMatchError.value = ''
  }
}

// 비밀번호 변경 시 일치 여부 확인
watch(() => form.value.password, () => {
  if (form.value.confirmPassword) {
    checkPasswordMatch()
  }
})

watch(() => props.visible, (newVal) => {
  if (newVal) {
    // 레이어 열릴 때 폼 초기화
    form.value = {
      userId: '',
      name: '',
      nickNm: '',
      email: '',
      password: '',
      confirmPassword: ''
    }
    error.value = ''
    userIdError.value = ''
    nicknameError.value = ''
    passwordMatchError.value = ''
    userIdChecked.value = false
    nicknameChecked.value = false
  }
})

const handleSignup = async () => {
  if (!isFormValid.value) {
    if (!isPasswordValid.value) {
      error.value = '비밀번호는 영문, 숫자, 특수문자를 포함하여 8자 이상이어야 합니다.'
    } else if (form.value.password !== form.value.confirmPassword) {
      error.value = '비밀번호가 일치하지 않습니다.'
    } else if (!userIdChecked.value || userIdError.value) {
      error.value = '아이디를 확인해주세요.'
    } else if (!nicknameChecked.value || nicknameError.value) {
      error.value = '닉네임을 확인해주세요.'
    } else {
      error.value = '모든 필드를 올바르게 입력해주세요.'
    }
    return
  }

  loading.value = true
  error.value = ''

  try {
    // 비밀번호 해시화
    const hashedPassword = await hashPassword(form.value.password)
    
    const result = await createUser({
      id: form.value.userId.trim(),
      name: form.value.name.trim(),
      nickNm: form.value.nickNm.trim(),
      email: form.value.email.trim(),
      password: hashedPassword, 
      avatar: '/icon/icon1.svg', // 기본 이미지 설정
      avatar_color: '#409EFF', // 기본 색상 설정
      del_yn: 'n',
      permission: 'pending', // 승인 대기 상태
      connection_status: 'offline',
      user_status: 'offline'
    })

    if (result.success) {
      emit('success', {
        userId: form.value.userId.trim(),
        message: '회원가입이 완료되었습니다. 관리자 승인 후 로그인할 수 있습니다.'
      })
      emit('update:visible', false)
    } else {
      error.value = result.error || '회원가입에 실패했습니다.'
    }
  } catch (err) {
    console.error('회원가입 오류:', err)
    error.value = '회원가입 중 오류가 발생했습니다.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.signup-layer {
  padding: 20px 0;
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

.error-message {
  margin-top: -8px;
}
</style>

