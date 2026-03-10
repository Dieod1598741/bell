import { backendService } from './backendService'
import { sseClient } from './sseClient'

export async function hashPassword(password) {
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

// 데이터 보강 공통 함수
const hydrateUser = (u, currentUserId = null) => {
  return {
    id: u.id || 'unknown',
    name: u.name || u.nickNm || u.id || '사용자',
    nickNm: u.nickNm || u.name || u.id || '사용자',
    avatar: u.avatar || '/icon/icon1.svg',
    userStatus: u.userStatus || 'offline',
    connectionStatus: u.connectionStatus || 'offline',
    permission: u.permission || 'approved',
    del_yn: u.del_yn || 'n',
    ...u
  }
}

export function watchUsers(callback, currentUserId = null) {
  // 1. 초기 데이터 로드
  const loadAndFilterUsers = async () => {
    const result = await backendService.getAllUsers()
    if (result.success) {
      console.log('[userService] watchUsers Raw:', result.data?.length);
      const users = (result.data || []).map(u => hydrateUser(u, currentUserId))
        .filter(u => {
          if (u.id === 'admin') return false;
          if (currentUserId && u.id === currentUserId) return false;
          // 삭제되지 않고 승격된 유저만 노출 (현업 기준 복구)
          const perm = (u.permission || '').toLowerCase();
          return u.del_yn !== 'y' && (perm === 'approved' || perm === 'admin');
        });
      console.log('[userService] watchUsers Result:', users.length);
      callback(users);
    }
  }

  loadAndFilterUsers()

  // 2. SSE 업데이트 감시
  const unsubscribe = sseClient.on('DB_UPDATE', (update) => {
    if (update.table === 'users') {
      loadAndFilterUsers()
    }
  })

  return unsubscribe
}

export function watchAllUsers(callback) {
  const loadUsers = async () => {
    const result = await backendService.getAllUsers()
    if (result.success) {
      const users = (result.data || []).map(u => hydrateUser(u))
        .filter(u => u.del_yn !== 'y');
      callback(users)
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
      const exists = (users.data || []).some(u => u.id === userId.trim())
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
      const exists = (users.data || []).some(u => (u.nickNm || '').trim().toLowerCase() === trimmedNickname)
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
      const allUsers = (result.data || []).map(u => hydrateUser(u))
        .filter(u => {
          if (u.id === 'admin') return false
          return u.del_yn !== 'y'
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
      const allUsers = (result.data || []).map(u => hydrateUser(u))
        .filter(u => u.del_yn !== 'y' && u.permission === 'pending')
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
