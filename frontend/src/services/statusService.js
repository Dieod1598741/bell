import { backendService } from './backendService'

export async function updateUserStatus(userId, status) {
  try {
    // 백엔드 API를 통해 로컬 및 DB 상태 동기 업데이트
    const result = await backendService.saveUserStatus(status)
    if (result.success) {
      console.log(`[statusService] 상태 업데이트 완료: ${status}`)
      return { success: true }
    } else {
      throw new Error(result.error || '상태 업데이트 실패')
    }
  } catch (error) {
    console.error('[statusService] 상태 업데이트 실패:', error)
    return { success: false, error: error.message || error }
  }
}
