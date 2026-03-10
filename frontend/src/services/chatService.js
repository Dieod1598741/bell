import { backendService } from './backendService'
import { sseClient } from './sseClient'

export function watchMessages(userId, currentUserId, callback) {
  // 1. 초기 메시지 로드
  const loadMessages = async () => {
    const result = await backendService.getMessages(userId, currentUserId)
    if (result.success) {
      callback(result.data)
    }
  }

  loadMessages()

  // 2. SSE 감시 (새 메시지 도착 시 로드)
  const unsubscribe = sseClient.on('NEW_CHAT', (msg) => {
    const isRelated = (msg.sender_user_id === userId && msg.target_user_id === currentUserId) ||
      (msg.sender_user_id === currentUserId && msg.target_user_id === userId)
    if (isRelated) {
      loadMessages()
    }
  })

  return unsubscribe
}

export function watchChats(currentUserId, callback) {
  // 채팅 목록 감시 (최근 메시지 기반)
  const loadChats = async () => {
    const result = await backendService.getRecentChats(currentUserId)
    if (result.success) {
      callback(result.data || [])
    }
  }

  loadChats()
  return sseClient.on('NEW_CHAT', () => loadChats())
}

export async function sendChatMessage(senderId, targetId, content) {
  return await backendService.sendChatMessage(senderId, targetId, content)
}

export async function markChatMessageRead(messageId) {
  return await backendService.markMessageRead(messageId, 'chat')
}

export async function loadMessagesPaged(userId, currentUserId, pageSize = 20, lastDoc = null) {
  try {
    const result = await backendService.getMessages(userId, currentUserId, 100) // 단순 페이징 생략
    if (result.success) {
      return {
        messages: result.data,
        lastDoc: result.data[result.data.length - 1],
        hasMore: false
      }
    }
    return { messages: [], lastDoc: null, hasMore: false }
  } catch (error) {
    console.error('[chatService] 채팅 메시지 로드 실패:', error)
    return { messages: [], lastDoc: null, hasMore: false }
  }
}

export async function getChatNotificationEnabled(userId, targetUserId) {
  // DB에서 알림 설정 조회 (추가 구현 필요)
  return { enabled: true }
}

export async function setChatNotificationEnabled(userId, targetUserId, enabled) {
  // DB에 알림 설정 저장 (추가 구현 필요)
  return { success: true }
}
