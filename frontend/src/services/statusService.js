import { db } from '@/firebase/config'
import { doc, updateDoc, serverTimestamp } from 'firebase/firestore'

export async function updateUserStatus(userId, status) {
  try {
    const userRef = doc(db, 'users', userId)
    await updateDoc(userRef, {
      user_status: status,
      updated_at: serverTimestamp()
    })
    return { success: true }
  } catch (error) {
    console.error('[statusService] 상태 업데이트 실패:', error)
    return { success: false, error }
  }
}
