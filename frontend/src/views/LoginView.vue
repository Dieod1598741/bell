<template>
  <div class="login-view absolute inset-0 w-full h-full flex items-center justify-center bg-gradient-to-br from-blue-50 to-blue-100">
    <div class="login-card bg-white rounded-lg shadow-xl p-8 w-full max-w-md mx-4">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-primary mb-2">Bell</h1>
        <p class="text-gray-600">알람 시스템</p>
      </div>

      <el-form 
        :model="loginForm" 
        @submit.prevent="handleLogin"
      >
        <div class="form-group-with-label">
          <span class="input-label-top">사용자 ID</span>
          <el-input
            v-model="loginForm.userId"
            placeholder="아무거나 입력하세요"
            @keyup.enter="handleLogin"
          />
        </div>

        <div class="form-group-with-label">
          <span class="input-label-top">비밀번호</span>
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="비밀번호를 입력하세요"
            show-password
            @keyup.enter="handleLogin"
          />
        </div>

        <!-- 아이디 저장, 자동 로그인 -->
        <div class="login-options">
          <el-checkbox v-model="saveUserId" @change="handleSaveUserIdChange">아이디 저장</el-checkbox>
          <el-checkbox v-model="autoLogin" @change="handleAutoLoginChange">자동 로그인</el-checkbox>
        </div>

        <el-button
          type="primary"
          class="w-full submit-button"
          @click="handleLogin"
          :loading="loading"
        >
          로그인
        </el-button>
        
        <div class="mt-4 text-center">
          <el-button
            link
            @click="showSignupLayer = true"
            class="text-gray-600 hover:text-primary"
          >
            회원가입
          </el-button>
        </div>
      </el-form>
    </div>

    <!-- 회원가입 레이어 -->
    <SignupLayer
      :visible="showSignupLayer"
      @update:visible="showSignupLayer = $event"
      @success="handleSignupSuccess"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import { getUser } from '@/services/userService'
import SignupLayer from '@/components/layers/SignupLayer.vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

// Firebase는 필수로 사용
import { setCurrentSession } from '@/composables/useSession'

const loginForm = ref({
  userId: '',
  password: ''
})

const loading = ref(false)
const showSignupLayer = ref(false)
const saveUserId = ref(false)
const autoLogin = ref(false)

// 저장된 아이디 불러오기
const loadSavedUserId = async () => {
  console.log('[LoginView] loadSavedUserId 호출')
  console.log('[LoginView] API 확인:', window.pywebview?.api ? '있음' : '없음')
  console.log('[LoginView] getLoginSettings 확인:', window.pywebview?.api?.getLoginSettings ? '있음' : '없음')
  
  // 백엔드 API에서 로그인 설정 조회
  if (window.pywebview?.api?.getLoginSettings) {
    try {
      console.log('[LoginView] 로그인 설정 조회 시도...')
      const result = await window.pywebview.api.getLoginSettings()
      console.log('[LoginView] 로그인 설정 조회 결과:', result)
      
      if (result.success && result.data) {
        const settings = result.data
        console.log('[LoginView] 로그인 설정 데이터:', settings)
        
        if (settings.saved_user_id) {
          loginForm.value.userId = settings.saved_user_id
          console.log('[LoginView] 저장된 아이디 복원:', settings.saved_user_id)
        }
        saveUserId.value = settings.save_user_id === true
        autoLogin.value = settings.auto_login === true
        console.log('[LoginView] 체크박스 상태 복원 - 아이디저장:', saveUserId.value, '자동로그인:', autoLogin.value)
        
        // 자동 로그인 체크되어 있으면 자동 로그인 시도 (비활성화됨)
        if (settings.auto_login && settings.saved_user_id) {
          handleAutoLogin(settings.saved_user_id)
        }
      } else {
        console.log('[LoginView] 저장된 로그인 설정 없음:', result.message || result.error)
      }
    } catch (e) {
      console.error('[LoginView] 로그인 설정 로드 실패:', e)
    }
  } else {
    console.log('[LoginView] API가 준비되지 않음')
  }
}

// 아이디 저장 체크박스 변경 시 백엔드에 저장
const handleSaveUserIdChange = async (checked) => {
  console.log('[LoginView] 아이디 저장 체크박스 변경:', checked, '현재 아이디:', loginForm.value.userId)
  
  if (window.pywebview?.api?.getLoginSettings && window.pywebview?.api?.saveLoginSettings) {
    try {
      const result = await window.pywebview.api.getLoginSettings()
      const settings = result.success && result.data ? result.data : {}
      
      if (!checked) {
        // 체크 해제 시 저장된 아이디 제거
        delete settings.saved_user_id
        settings.save_user_id = false
        console.log('[LoginView] 아이디 저장 해제')
      } else {
        // 체크 시 현재 아이디 저장
        if (loginForm.value.userId.trim()) {
          settings.saved_user_id = loginForm.value.userId.trim()
          settings.save_user_id = true
          console.log('[LoginView] 아이디 저장:', settings.saved_user_id)
        } else {
          console.log('[LoginView] 아이디가 비어있어서 저장하지 않음')
        }
      }
      
      const saveResult = await window.pywebview.api.saveLoginSettings(settings)
      console.log('[LoginView] 아이디 저장 결과:', saveResult)
    } catch (e) {
      console.error('[LoginView] 로그인 설정 저장 실패:', e)
    }
  } else {
    console.log('[LoginView] API가 준비되지 않음')
  }
}

// 자동 로그인 체크박스 변경 시 백엔드에 저장
const handleAutoLoginChange = async (checked) => {
  if (window.pywebview?.api?.getLoginSettings && window.pywebview?.api?.saveLoginSettings) {
    try {
      const result = await window.pywebview.api.getLoginSettings()
      const settings = result.success && result.data ? result.data : {}
      settings.auto_login = checked
      await window.pywebview.api.saveLoginSettings(settings)
    } catch (e) {
      console.error('[LoginView] 로그인 설정 저장 실패:', e)
    }
  }
}

// 자동 로그인 처리
const handleAutoLogin = async (userId) => {
  console.log('[LoginView] 자동 로그인 시도:', userId)
  
  // 백엔드에서 저장된 사용자 정보 확인
  if (window.pywebview?.api?.getUserInfo) {
    try {
      const userResult = await window.pywebview.api.getUserInfo()
      if (userResult?.success && userResult?.data) {
        // 이미 로그인된 상태면 메인으로 이동
        const userData = userResult.data
        if (userData.id === userId) {
          console.log('[LoginView] 이미 로그인된 상태 - 메인으로 이동')
          userStore.setUser(userData)
          router.push('/main')
          return
        }
      }
    } catch (e) {
      console.error('[LoginView] 자동 로그인 확인 실패:', e)
    }
  }
  
  // 저장된 사용자 정보가 없으면 자동 로그인 불가
  console.log('[LoginView] 자동 로그인 불가 - 저장된 사용자 정보 없음')
}

// 알림 테스트 실행
const runNotificationTest = async () => {
  if (!window.pywebview?.api?.runNotificationTest) {
    ElMessage.warning('알림 테스트 API를 사용할 수 없습니다.')
    return
  }
  
  testLoading.value = true
  try {
    const result = await window.pywebview.api.runNotificationTest()
    if (result.success) {
      ElMessage.success('알림 테스트가 실행되었습니다. 애플리케이션에서 알림을 확인해주세요.')
      console.log('[알림 테스트] 출력:', result.output)
    } else {
      ElMessage.error(`알림 테스트 실패: ${result.error || '알 수 없는 오류'}`)
      console.error('[알림 테스트] 오류:', result.output)
    }
  } catch (error) {
    console.error('[알림 테스트] 실행 오류:', error)
    ElMessage.error('알림 테스트 실행 중 오류가 발생했습니다.')
  } finally {
    testLoading.value = false
  }
}

onMounted(async () => {
  // 이미 로그인된 상태인지 확인
  if (userStore.isLoggedIn && userStore.user) {
    // 이미 로그인되어 있으면 메인으로 리다이렉트
    router.replace('/main')
    return
  }
  
  // 자동 로그인 체크 (App.vue에서 처리되지 않은 경우)
  if (window.pywebview?.api?.getLoginSettings) {
    try {
      const settingsResult = await window.pywebview.api.getLoginSettings()
      if (settingsResult.success && settingsResult.data) {
        const settings = settingsResult.data
        if (settings.auto_login && settings.saved_user_id) {
          const userId = settings.saved_user_id
          if (window.pywebview?.api?.getUserInfo) {
            const userResult = await window.pywebview.api.getUserInfo()
            if (userResult?.success && userResult?.data) {
              const userData = userResult.data
              if (userData.id === userId) {
                await userStore.setUser(userData)
                router.replace('/main')
                return
              }
            }
          }
        }
      }
    } catch (e) {
      console.error('[LoginView] 자동 로그인 체크 실패:', e)
    }
  }
  
  // API가 준비될 때까지 대기 후 로그인 설정 로드
  let retryCount = 0
  const maxRetries = 10
  
  const tryLoadSettings = async () => {
    if (window.pywebview?.api?.getLoginSettings) {
      await loadSavedUserId()
    } else if (retryCount < maxRetries) {
      retryCount++
      setTimeout(tryLoadSettings, 200)
    } else {
      console.log('[LoginView] API 준비 대기 시간 초과')
    }
  }
  
  tryLoadSettings()
})

// 비밀번호 해시화 함수
const hashPassword = (password) => {
  // 간단한 SHA-256 해시 (프로덕션에서는 더 안전한 방법 사용 권장)
  const encoder = new TextEncoder()
  const data = encoder.encode(password)
  return crypto.subtle.digest('SHA-256', data).then(hashBuffer => {
    const hashArray = Array.from(new Uint8Array(hashBuffer))
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
  })
}

const handleLogin = async () => {
  if (!loginForm.value.userId.trim() || !loginForm.value.password.trim()) {
    ElMessage.warning('아이디와 비밀번호를 입력해주세요.')
    return
  }

  loading.value = true
  
  try {
    const userId = loginForm.value.userId.trim()
    const password = loginForm.value.password.trim()
    
    console.log('[Login] 로그인 시도:', userId)
    
    // Firestore에서 사용자 확인
    console.log('[Login] Firestore에서 사용자 조회 중...')
    let user
    try {
      // 타임아웃 설정 (10초로 증가)
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('타임아웃')), 10000)
      )
      user = await Promise.race([getUser(userId), timeoutPromise])
    } catch (error) {
      console.error('[Login] 사용자 조회 오류:', error)
      console.error('[Login] 에러 상세:', error.code, error.message, error.stack)
      
      if (error.message === '타임아웃') {
        ElMessage.error('서버 연결 시간이 초과되었습니다. Firebase 설정과 보안 규칙을 확인해주세요.')
      } else if (error.code === 'permission-denied') {
        ElMessage.error('권한이 거부되었습니다. Firestore 보안 규칙을 확인해주세요. (개발용 규칙: allow read, write: if true)')
      } else if (error.code === 'unavailable') {
        ElMessage.error('Firebase 서비스를 사용할 수 없습니다. 네트워크 연결을 확인해주세요.')
      } else {
        ElMessage.error(`사용자 조회 중 오류가 발생했습니다: ${error.message || error.code || error}`)
      }
      loading.value = false
      return
    }
    console.log('[Login] 사용자 조회 결과:', user ? '찾음' : '없음', user ? { id: user.id, name: user.name, permission: user.permission } : null)
    
    if (!user) {
      ElMessage.error('사용자를 찾을 수 없습니다. 아이디를 확인해주세요.')
      loading.value = false
      return
    }
    
    // 비밀번호 확인
    console.log('[Login] 비밀번호 검증 중...')
    const hashedPassword = await hashPassword(password)
    console.log('[Login] 입력한 비밀번호 해시:', hashedPassword.substring(0, 10) + '...')
    console.log('[Login] 저장된 비밀번호 해시:', user.password ? user.password.substring(0, 10) + '...' : '없음')
    
    if (!user.password) {
      ElMessage.error('비밀번호가 설정되지 않은 계정입니다. 관리자에게 문의하세요.')
      loading.value = false
      return
    }
    
    if (user.password !== hashedPassword) {
      ElMessage.error('비밀번호가 일치하지 않습니다.')
      loading.value = false
      return
    }
    
    if (user.permission !== 'approved' && user.permission !== 'admin') {
      ElMessage.warning('승인 대기 중입니다. 관리자 승인 후 로그인할 수 있습니다.')
      loading.value = false
      return
    }
    
    await userStore.setUser({
      id: user.id,
      name: user.name,
      email: user.email,
      permission: user.permission,
      user_status: 'online'
    })
    
    const { updateUserStatus } = await import('@/services/statusService')
    await updateUserStatus(user.id, 'online')
    
    console.log('[Login] setUser 완료, isLoggedIn:', userStore.isLoggedIn, 'user:', userStore.user?.id)
    
    // isLoggedIn 확인
    if (!userStore.isLoggedIn) {
      console.error('[Login] 사용자 정보 저장 후에도 로그인 상태가 false입니다')
      ElMessage.error('로그인 상태 저장에 실패했습니다.')
      loading.value = false
      return
    }

    // 백엔드가 사용자 ID를 감지할 수 있도록 세션 저장
    try {
      await setCurrentSession(user.id)
      console.log('[Login] 세션 저장 완료:', user.id)
    } catch (error) {
      console.error('[Login] 세션 저장 실패:', error)
    }

    // 로그인 설정 저장 (하드웨어 ID별)
    if (window.pywebview?.api?.saveLoginSettings) {
      try {
        // 기존 설정 불러오기
        const getResult = await window.pywebview.api.getLoginSettings()
        const existingSettings = getResult.success && getResult.data ? getResult.data : {}
        
        // 로그인 성공 시 설정 업데이트
        const settings = {
          ...existingSettings,
          saved_user_id: saveUserId.value ? userId : (existingSettings.saved_user_id || null),
          save_user_id: saveUserId.value,
          auto_login: autoLogin.value
        }
        
        // 아이디 저장이 체크 해제된 경우 아이디 제거
        if (!saveUserId.value) {
          delete settings.saved_user_id
        }
        
        const saveResult = await window.pywebview.api.saveLoginSettings(settings)
        console.log('[Login] 로그인 설정 저장 완료:', saveResult, '설정:', settings)
      } catch (e) {
        console.error('[Login] 로그인 설정 저장 실패:', e)
      }
    }

    // 메인 화면으로 이동
    console.log('[Login] ===== 메인 화면으로 이동 시작 =====')
    console.log('[Login] isLoggedIn:', userStore.isLoggedIn)
    console.log('[Login] user:', userStore.user?.id)
    loading.value = false
    
    // 즉시 라우터 이동 (대기 없이)
    console.log('[Login] router.push 호출')
    router.push('/main').then(() => {
      console.log('[Login] router.push 성공')
    }).catch((error) => {
      console.error('[Login] router.push 실패:', error)
      // 강제로 메인으로 이동
      console.log('[Login] window.location.href로 강제 이동')
      window.location.href = '/main'
    })
  } catch (error) {
    console.error('로그인 실패:', error)
    ElMessage.error('로그인 중 오류가 발생했습니다.')
  } finally {
    loading.value = false
  }
}

const handleSignupSuccess = (data) => {
  ElMessage.success(data.message)
  showSignupLayer.value = false
}
</script>

<style scoped>
.login-card {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.form-group-with-label {
  position: relative;
  margin-bottom: 24px;
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

.login-options {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
  font-size: 14px;
}

.submit-button {
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
  margin-top: 8px;
}

:deep(.el-input__wrapper) {
  border-radius: 12px;
  padding: 8px 16px;
  min-height: 40px;
}
</style>

