/**세션 관리 (프론트엔드) - 백엔드가 로그인 상태를 감지하기 위한 세션 관리*/
import { doc, setDoc, deleteDoc, serverTimestamp } from 'firebase/firestore'
import { db } from '@/firebase/config'

// 세션 복원 중복 실행 방지
let sessionRestoreInProgress = false
let lastRestoredUserId = null

/**
 * 현재 세션 저장 (백엔드가 사용자 ID를 감지하기 위해)
 * @param {string} userId - 사용자 ID
 * @returns {Promise<{success: boolean, error?: string}>}
 */
export async function setCurrentSession(userId) {
  try {
    console.log('[Session] 세션 저장 시도: user_id=', userId)
    if (!db) {
      console.error('[Session] db가 초기화되지 않았습니다')
      return { success: false, error: 'db not initialized' }
    }
    const sessionRef = doc(db, 'current_sessions', 'backend')
    console.log('[Session] 세션 문서 참조 생성:', sessionRef.path)
    await setDoc(sessionRef, {
      user_id: userId,
      updated_at: serverTimestamp()
    }, { merge: true })
    console.log('[Session] ✅ 세션 저장 성공: user_id=', userId)
    return { success: true }
  } catch (error) {
    console.error('[Session] ❌ 세션 저장 실패:', error)
    console.error('[Session] 에러 상세:', error.message, error.stack)
    return { success: false, error: error.message }
  }
}

/**
 * 현재 세션 삭제 (로그아웃 시)
 * @returns {Promise<{success: boolean, error?: string}>}
 */
export async function clearCurrentSession() {
  try {
    console.log('[Session] 세션 삭제 시도')
    if (!db) {
      console.error('[Session] db가 초기화되지 않았습니다')
      return { success: false, error: 'db not initialized' }
    }
    const sessionRef = doc(db, 'current_sessions', 'backend')
    await deleteDoc(sessionRef)
    console.log('[Session] ✅ 세션 삭제 성공')
    lastRestoredUserId = null
    return { success: true }
  } catch (error) {
    console.error('[Session] ❌ 세션 삭제 실패:', error)
    return { success: false, error: error.message }
  }
}

/**
 * 세션 복원 (localStorage에서 사용자 정보 확인 후 세션 저장)
 * @returns {Promise<{success: boolean, userId?: string, error?: string}>}
 */
export async function restoreSession() {
  // 중복 실행 방지
  if (sessionRestoreInProgress) {
    return { success: false, error: 'already in progress' }
  }
  
  // 백엔드 API에서 사용자 정보 확인
  let userId = null
  
  if (window.pywebview?.api?.getUserInfo) {
    try {
      const result = await window.pywebview.api.getUserInfo()
      if (result.success && result.data) {
        userId = result.data?.id
      }
    } catch (e) {
      console.error('[Session] 사용자 정보 조회 실패:', e)
      return { success: false, error: 'api error' }
    }
  }
  
  // 사용자 ID가 없으면 복원 불가
  if (!userId) {
    lastRestoredUserId = null
    return { success: false, error: 'no user' }
  }
  
  // 같은 사용자 ID면 스킵
  if (lastRestoredUserId === userId) {
    return { success: true, userId }
  }
  
  // 세션 저장
  sessionRestoreInProgress = true
  try {
    const result = await setCurrentSession(userId)
    if (result.success) {
      lastRestoredUserId = userId
      return { success: true, userId }
    } else {
      return { success: false, error: result.error }
    }
  } catch (error) {
    console.error('[Session] ❌ 세션 복원 오류:', error)
    return { success: false, error: error.message }
  } finally {
    sessionRestoreInProgress = false
  }
}

/**
 * 세션 복원 상태 초기화 (로그아웃 시)
 */
export function resetSessionRestore() {
  lastRestoredUserId = null
  sessionRestoreInProgress = false
  console.log('[Session] 세션 복원 상태 초기화')
}

