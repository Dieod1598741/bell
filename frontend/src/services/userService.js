import { backendService } from './backendService'
import { sseClient } from './sseClient'

async function hashPassword(password) {
  const encoder = new TextEncoder()
  const data = encoder.encode(password)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

export async function getUser(userId) {
  try {
    if (!userId) return null
    const result = await backendService.getUserById(userId)
    if (result.success && result.data) {
      return result.data
    }
    return null
  } catch (error) {
    console.error('[userService] 사용자 조회 실패:', error)
    throw error
  }
}

export function watchUsers(callback, currentUserId = null) {
  // 1. 초기 데이터 로드
  const loadAndFilterUsers = async () => {
    const result = await backendService.getAllUsers()
    if (result.success) {
      const users = result.data.filter(u => {
        if (u.id === 'admin') return false
        if (currentUserId && u.id === currentUserId) return false
        return u.del_yn === 'n' && (u.permission === 'approved' || u.permission === 'admin')
      })
      callback(users)
    }
  }

  loadAndFilterUsers()

  // 2. SSE 업데이트 감시
  const unsubscribe = sseClient.on('DB_UPDATE', (update) => {
    if (update.table === 'users') {
      loadAndFilterUsers()
    }
  })

  // SSE 업데이트 감시 (구독 취소 함수 반환)
  return unsubscribe
}

export function watchAllUsers(callback) {
  const loadUsers = async () => {
    const result = await backendService.getAllUsers()
    if (result.success) {
      callback(result.data.filter(u => u.del_yn !== 'y'))
    }
  }

  loadUsers()
  return sseClient.on('DB_UPDATE', (update) => {
    if (update.table === 'users') loadUsers()
  })
}

export async function createUser(userData) {
  try {
    const result = await backendService.saveUserInfo(userData)
    return result
  } catch (error) {
    console.error('[userService] 사용자 생성 실패:', error)
    return { success: false, error: error.message }
  }
}

export async function updateUserProfile(userId, updateData) {
  try {
    return await backendService.saveUserInfo({ id: userId, ...updateData })
  } catch (error) {
    console.error('[userService] 사용자 프로필 업데이트 실패:', error)
    return { success: false, error: error.message }
  }
}

export async function updateUserPermission(userId, permission) {
  try {
    return await backendService.saveUserInfo({ id: userId, permission })
  } catch (error) {
    console.error('[userService] 권한 변경 실패:', error)
    return { success: false, error: error.message }
  }
}

export async function addUserByAdmin(userData) {
  return createUser({
    ...userData,
    permission: userData.permission || 'approved'
  })
}

export async function checkUserIdExists(userId) {
  try {
    const users = await backendService.getAllUsers()
    if (users.success) {
      const exists = users.data.some(u => u.id === userId.trim())
      return { exists }
    }
    return { exists: false }
  } catch (error) {
    console.error('[userService] 아이디 중복 검증 실패:', error)
    return { exists: false, error: error.message }
  }
}

export async function checkNicknameExists(nickname) {
  try {
    const users = await backendService.getAllUsers()
    if (users.success) {
      const trimmedNickname = nickname.trim().toLowerCase()
      const exists = users.data.some(u => (u.nickNm || '').trim().toLowerCase() === trimmedNickname)
      return { exists }
    }
    return { exists: false }
  } catch (error) {
    console.error('[userService] 닉네임 중복 검증 실패:', error)
    return { exists: false, error: error.message }
  }
}

export async function loadUsers(pageSize = 20, lastDoc = null) {
  try {
    const result = await backendService.getAllUsers()
    if (result.success) {
      const allUsers = result.data.filter(u => {
        if (u.id === 'admin') return false
        return u.del_yn === 'n' && (u.permission === 'approved' || u.permission === 'admin')
      })

      const startIndex = lastDoc ? allUsers.findIndex(u => u.id === lastDoc.id) + 1 : 0
      const users = allUsers.slice(startIndex, startIndex + pageSize)
      return {
        users,
        lastDoc: users.length > 0 ? users[users.length - 1] : null,
        hasMore: startIndex + pageSize < allUsers.length
      }
    }
    return { users: [], lastDoc: null, hasMore: false }
  } catch (error) {
    console.error('[userService] 사용자 목록 로드 실패:', error)
    return { users: [], lastDoc: null, hasMore: false }
  }
}

export async function loadPendingUsers(pageSize = 20, lastDoc = null) {
  try {
    const result = await backendService.getAllUsers()
    if (result.success) {
      const allUsers = result.data.filter(u => u.del_yn === 'n' && u.permission === 'pending')
      const startIndex = lastDoc ? allUsers.findIndex(u => u.id === lastDoc.id) + 1 : 0
      const users = allUsers.slice(startIndex, startIndex + pageSize)
      return {
        users,
        lastDoc: users.length > 0 ? users[users.length - 1] : null,
        hasMore: startIndex + pageSize < allUsers.length
      }
    }
    return { users: [], lastDoc: null, hasMore: false }
  } catch (error) {
    console.error('[userService] 승인 대기 사용자 조회 실패:', error)
    return { users: [], lastDoc: null, hasMore: false }
  }
}
