/**
 * 사용자 상태 관리 유틸리티
 */

export const STATUS_COLORS = {
  online: 'bg-green-500',
  away: 'bg-orange-500',
  do_not_disturb: 'bg-red-500',
  offline: 'bg-gray-300' // 더 밝은 회색
}

export const STATUS_LABELS = {
  online: '온라인',
  away: '자리비움',
  do_not_disturb: '방해금지',
  offline: '오프라인'
}

export const STATUS_LIST = [
  { value: 'online', label: '온라인', color: STATUS_COLORS.online },
  { value: 'away', label: '자리비움', color: STATUS_COLORS.away },
  { value: 'do_not_disturb', label: '방해금지', color: STATUS_COLORS.do_not_disturb },
  { value: 'offline', label: '오프라인', color: STATUS_COLORS.offline }
]

/**
 * 상태에 따른 색상 클래스 반환
 * @param {string} status - 사용자 상태
 * @returns {string} Tailwind CSS 클래스
 */
export function getStatusColor(status) {
  return STATUS_COLORS[status] || STATUS_COLORS.offline
}

/**
 * 상태에 따른 라벨 반환
 * @param {string} status - 사용자 상태
 * @returns {string} 상태 라벨
 */
export function getStatusLabel(status) {
  return STATUS_LABELS[status] || STATUS_LABELS.offline
}

/**
 * 오프라인 상태인지 확인
 * @param {string} status - 사용자 상태
 * @returns {boolean}
 */
export function isOffline(status) {
  return status === 'offline'
}








