import { backendService } from './backendService'
import { sseClient } from './sseClient'

export function watchInbox(userId, callback) {
  const loadInbox = async () => {
    const result = await backendService.getInbox(userId)
    if (result.success) {
      callback(result.data)
    }
  }

  loadInbox()

  // NEW_CHAT 이나 DB_UPDATE 이벤트를 이벤트로 활용 가능 (백엔드에서 NEW_INBOX 를 보내게 할 수도 있음)
  const unsubscribe = sseClient.on('DB_UPDATE', (update) => {
    if (update.table === 'inbox' || update.table === 'chats') {
      loadInbox()
    }
  })

  return unsubscribe
}

export async function sendInboxMessage(senderId, targetId, content, type = 'message', extraData = {}) {
  // 실제 백엔드에 구현된 API가 있으면 호출, 없으면 generic 저장 API 필요
  // 현재는 chatService에서 유사 기능 수행 가능
  return { success: true }
}

export async function markInboxMessageRead(messageId) {
  return await backendService.markMessageRead(messageId, 'inbox')
}

export async function markAllInboxAsRead(userId) {
  // 백엔드에 구현 필요
  return { success: true }
}

export async function deleteInboxMessage(messageId) {
  // 백엔드에 구현 필요 (del_yn = 'y' 처리)
  return { success: true }
}

export async function loadInboxPaged(userId, pageSize = 20, lastDoc = null) {
  try {
    const result = await backendService.getInbox(userId, 100)
    if (result.success) {
      return {
        messages: result.data,
        lastDoc: result.data[result.data.length - 1],
        hasMore: false
      }
    }
    return { messages: [], lastDoc: null, hasMore: false }
  } catch (error) {
    console.error('[inboxService] 인박스 로드 실패:', error)
    return { messages: [], lastDoc: null, hasMore: false }
  }
}

export async function markMessageRead(messageId, collectionName = null) {
  const type = collectionName === 'inbox' ? 'inbox' : 'chat'
  return await backendService.markMessageRead(messageId, type)
}
