/**
 * 사용자 표시 이름 관련 유틸리티
 * 닉네임이 있으면 닉네임을, 없으면 이름을 반환
 */

/**
 * 사용자의 표시 이름 가져오기 (닉네임 우선)
 * @param {Object} user - 사용자 객체
 * @returns {string} 표시할 이름
 */
export function getDisplayName(user) {
  if (!user) return '사용자'
  return user.nickNm || user.name || user.id || '사용자'
}

/**
 * 사용자의 이니셜 가져오기 (닉네임 우선)
 * @param {Object} user - 사용자 객체
 * @returns {string} 이니셜 (첫 글자)
 */
export function getDisplayInitial(user) {
  if (!user) return '?'
  const displayName = getDisplayName(user)
  return displayName?.charAt(0)?.toUpperCase() || '?'
}








