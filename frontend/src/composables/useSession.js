/**세션 관리 (프론트엔드) - 백엔드와 로컬 저장소를 공유하므로 Firebase 세션은 더 이상 필요하지 않음*/
export async function setCurrentSession(userId) {
  console.log('[Session] 세션 설정 완료 (로컬):', userId)
  return { success: true }
}

export async function clearCurrentSession() {
  console.log('[Session] 세션 삭제 완료')
  return { success: true }
}

export async function restoreSession() {
  // 백엔드 API에서 사용자 정보 확인
  if (window.pywebview?.api?.getUserInfo) {
    try {
      const result = await window.pywebview.api.getUserInfo()
      if (result.success && result.data) {
        return { success: true, userId: result.data.id }
      }
    } catch (e) {
      console.error('[Session] 세션 복원 실패:', e)
    }
  }
  return { success: false }
}

export function resetSessionRestore() {
  console.log('[Session] 세션 복원 상태 초기화')
}

