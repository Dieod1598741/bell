import firebase_admin
from firebase_admin import credentials, firestore
import argparse
import sys
import os

def init_firebase():
    # 서비스 계정 키 파일 경로
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, 'firebase-service-account.json')
    
    if not os.path.exists(json_path):
        print(f"❌ 에러: {json_path} 파일을 찾을 수 없습니다.")
        return None
    
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(json_path)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        print(f"❌ Firebase 초기화 실패: {e}")
        return None

def list_pending_users(db):
    print("🔍 승인 대기 중인 사용자 목록 조회 중...")
    try:
        users_ref = db.collection('users')
        query = users_ref.where('permission', '==', 'pending').stream()
        
        pending_users = []
        for doc in query:
            user_data = doc.to_dict()
            pending_users.append({
                'id': doc.id,
                'name': user_data.get('name', 'N/A'),
                'nickNm': user_data.get('nickNm', 'N/A'),
                'email': user_data.get('email', 'N/A'),
                'created_at': user_data.get('created_at', 'N/A')
            })
        
        if not pending_users:
            print("✅ 승인 대기 중인 사용자가 없습니다.")
        else:
            print(f"📋 총 {len(pending_users)}명의 대기자가 있습니다:")
            for user in pending_users:
                print(f"- ID: {user['id']} | 이름: {user['name']} | 닉네임: {user['nickNm']} | 이메일: {user['email']}")
        return pending_users
    except Exception as e:
        print(f"❌ 사용자 조회 실패: {e}")
        return []

def approve_user(db, user_id):
    print(f"🚀 사용자 승인 시도 중: {user_id}")
    try:
        user_ref = db.collection('users').document(user_id)
        doc = user_ref.get()
        
        if not doc.exists:
            print(f"❌ 에러: ID가 '{user_id}'인 사용자를 찾을 수 없습니다.")
            return False
        
        user_ref.update({
            'permission': 'approved',
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        print(f"✅ 성공: 사용자 '{user_id}'가 승인되었습니다! 이제 로그인이 가능합니다.")
        return True
    except Exception as e:
        print(f"❌ 승인 실패: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bell 사용자 승인 툴')
    parser.add_argument('--list', action='store_true', help='승인 대기 중인 사용자 목록 표시')
    parser.add_argument('--approve', type=str, help='승인할 사용자 ID')
    
    args = parser.parse_args()
    
    db = init_firebase()
    if not db:
        sys.exit(1)
        
    if args.list:
        list_pending_users(db)
    elif args.approve:
        approve_user(db, args.approve)
    else:
        parser.print_help()
