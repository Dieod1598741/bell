// Firebase 설정
// Firebase Console에서 설정 정보를 가져와서 입력하세요

import { initializeApp } from 'firebase/app'
import { getFirestore } from 'firebase/firestore'
import { getAuth } from 'firebase/auth'

// Firebase 설정 정보
// projectId는 firebase-service-account.json에서 확인: bell-6dfbb
// 나머지 정보는 Firebase Console → 프로젝트 설정 → 일반 → 내 앱 (웹 앱)에서 가져오세요
const firebaseConfig = {
    apiKey: "AIzaSyDubJSk6QoN3eJLTJNftouoslj_9Pj6aeQ",
    authDomain: "bell-6dfbb.firebaseapp.com",
    projectId: "bell-6dfbb",
    storageBucket: "bell-6dfbb.firebasestorage.app",
    messagingSenderId: "744032491898",
    appId: "1:744032491898:web:d2117e9ad961db223edec3",
    measurementId: "G-739YLW9748"
}


// Firebase 초기화
let app, db, auth

try {
  // Firebase 설정 확인
  if (firebaseConfig.projectId === 'YOUR_PROJECT_ID' || 
      firebaseConfig.apiKey === 'YOUR_API_KEY') {
    console.error('[Firebase] ❌ Firebase 설정이 필요합니다!')
    console.error('[Firebase] Firebase Console에서 설정 정보를 가져와서 입력하세요.')
    console.error('[Firebase] 설정 방법:')
    console.error('  1. Firebase Console → 프로젝트 설정 → 일반')
    console.error('  2. "내 앱" 섹션에서 웹 앱 선택 (없으면 추가)')
    console.error('  3. 설정 정보를 복사하여 아래 firebaseConfig에 입력')
    console.error('')
    console.error('현재 설정 상태:')
    console.error('  projectId:', firebaseConfig.projectId)
    console.error('  apiKey:', firebaseConfig.apiKey ? firebaseConfig.apiKey.substring(0, 10) + '...' : '없음')
    
    // 개발 중이므로 에러를 throw하지 않고 경고만 표시
    // 실제 Firebase 설정이 완료되면 정상 작동
    console.warn('[Firebase] ⚠️ Firebase 설정이 완료될 때까지 일부 기능이 작동하지 않을 수 있습니다.')
  }
  
  app = initializeApp(firebaseConfig)
  
  // Firestore 초기화
  db = getFirestore(app)
  auth = getAuth(app)
  
  if (firebaseConfig.projectId !== 'YOUR_PROJECT_ID') {
    console.log('[Firebase] ✅ Firebase 초기화 완료:', firebaseConfig.projectId)
    console.log('[Firebase] 설정 정보:', {
      projectId: firebaseConfig.projectId,
      authDomain: firebaseConfig.authDomain
    })
  }
} catch (error) {
  console.error('[Firebase] ❌ Firebase 초기화 실패:', error)
  console.error('[Firebase] 에러 상세:', error.message)
  // 개발 중이므로 에러를 throw하지 않고 경고만 표시
  console.warn('[Firebase] ⚠️ Firebase 초기화 실패했지만 계속 진행합니다.')
}

export { db, auth }

