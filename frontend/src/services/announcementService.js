import { backendService } from './backendService'
import { sseClient } from './sseClient'

export async function sendAnnouncement(userIds, message, senderId = 'admin') {
  return await backendService.sendAnnouncement(userIds, message, senderId)
}

export function watchAnnouncements(userId, callback) {
  const loadAnnouncements = async () => {
    const result = await backendService.getInbox(userId) // 공지도 인박스 테이블에 같이 쌓이는 구조라면
    if (result.success) {
      callback(result.data.filter(f => f.type === 'announcement'))
    }
  }

  loadAnnouncements()

  const unsubscribe = sseClient.on('NEW_ANNOUNCEMENT', () => loadAnnouncements())
  return unsubscribe
}

export async function markAnnouncementRead(announcementId) {
  return await backendService.markMessageRead(announcementId, 'inbox')
}



