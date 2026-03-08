import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const isLoggedIn = ref(false)
  const userStatus = ref('online') // online, away, do_not_disturb, offline

  const setUser = async (userData) => {
    const userId = userData?.id
    let finalUserData = userData
    
    if (userId) {
      try {
        const { getUser } = await import('@/services/userService')
        const firestoreUser = await getUser(userId)
        
        if (firestoreUser) {
          finalUserData = {
            ...userData,
            ...firestoreUser,
            id: userData.id || firestoreUser.id
          }
        }
      } catch (e) {
        console.error('[userStore] Firestore 정보 로드 실패:', e)
      }
    }
    
    user.value = finalUserData
    isLoggedIn.value = true
    if (finalUserData.user_status) {
      userStatus.value = finalUserData.user_status
    }
    
    if (window.pywebview?.api?.saveUserInfo) {
      await window.pywebview.api.saveUserInfo(finalUserData)
      if (finalUserData.user_status) {
        await window.pywebview.api.saveUserStatus(finalUserData.user_status)
      }
    }
  }

  const setStatus = async (status) => {
    userStatus.value = status
    if (user.value) {
      user.value.user_status = status
    }
    
    const userId = user.value?.id
    if (userId) {
      try {
        const { updateUserStatus } = await import('@/services/statusService')
        await updateUserStatus(userId, status)
      } catch (e) {
        console.error('[userStore] 상태 업데이트 실패:', e)
      }
    }
  }

  const getStatusLabel = computed(() => {
    const labels = {
      online: '온라인',
      away: '자리비움',
      do_not_disturb: '방해금지',
      offline: '오프라인'
    }
    return labels[userStatus.value] || '오프라인'
  })

  const logout = async () => {
    const currentUserId = user.value?.id
    
    if (currentUserId) {
      try {
        const { updateUserStatus } = await import('@/services/statusService')
        await updateUserStatus(currentUserId, 'offline')
      } catch (error) {
        console.error('[userStore] 상태 업데이트 실패:', error)
      }
    }
    
    if (window.pywebview?.api) {
      if (window.pywebview.api.deleteUserInfo) {
        await window.pywebview.api.deleteUserInfo()
      }
      if (window.pywebview.api.getLoginSettings && window.pywebview.api.saveLoginSettings) {
        const settingsResult = await window.pywebview.api.getLoginSettings()
        if (settingsResult.success && settingsResult.data) {
          const settings = settingsResult.data
          settings.auto_login = false
          await window.pywebview.api.saveLoginSettings(settings)
        }
      }
    }
    
    user.value = null
    isLoggedIn.value = false
    userStatus.value = 'offline'
  }

  const loadUser = async () => {
    if (window.pywebview?.api?.getUserInfo) {
      try {
        const userResult = await window.pywebview.api.getUserInfo()
        const statusResult = await window.pywebview.api.getUserStatus()
        
        if (userResult?.success && userResult?.data) {
          let userData = userResult.data
          const userId = userData.id
          
          try {
            const { getUser } = await import('@/services/userService')
            const firestoreUser = await getUser(userId)
            
            if (firestoreUser) {
              userData = {
                ...userData,
                ...firestoreUser,
                id: userData.id || firestoreUser.id
              }
            }
          } catch (e) {
            console.error('[userStore] Firestore 정보 로드 실패:', e)
          }
          
          user.value = userData
          isLoggedIn.value = true
          
          if (statusResult?.success && statusResult?.data) {
            userStatus.value = statusResult.data
            user.value.user_status = statusResult.data
          } else if (userData.user_status) {
            userStatus.value = userData.user_status
          }
        }
      } catch (e) {
        console.error('[userStore] 사용자 정보 로드 실패:', e)
      }
    }
  }

  const updateUser = async (userData) => {
    const currentUserId = user.value?.id
    if (!currentUserId) {
      return { success: false, error: '사용자 ID가 없습니다' }
    }
    
    try {
      const { updateUserProfile } = await import('@/services/userService')
      const firestoreResult = await updateUserProfile(currentUserId, userData)
      
      if (!firestoreResult.success) {
        return { success: false, error: firestoreResult.error }
      }
    } catch (e) {
      return { success: false, error: e.message }
    }
    
    if (window.pywebview?.api?.updateUserInfo) {
      await window.pywebview.api.updateUserInfo(userData)
    }
    
    try {
      const { getUser } = await import('@/services/userService')
      const latestUser = await getUser(currentUserId)
      
      if (latestUser) {
        user.value = { ...user.value, ...latestUser }
      } else {
        user.value = { ...user.value, ...userData }
      }
    } catch (e) {
      user.value = { ...user.value, ...userData }
    }
    
    return { success: true }
  }

  // 초기화 시 저장된 사용자 정보 로드
  loadUser()

  return {
    user,
    isLoggedIn,
    userStatus,
    getStatusLabel,
    setUser,
    setStatus,
    logout,
    loadUser,
    updateUser
  }
})

