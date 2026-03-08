import argparse
import sys
import os

# 상위 디렉토리를 경로에 추가하여 db_manager 임포트 가능하게 함
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from db_manager import DBManager

def list_pending_users(db):
    print("🔍 승인 대기 중인 사용자 목록 조회 중 (Supabase)...")
    try:
        query = "SELECT id, name, nick_nm, email, created_at FROM users WHERE permission = 'pending' AND del_yn = 'n'"
        pending_users = db.execute_query(query)
        
        if not pending_users:
            print("✅ 승인 대기 중인 사용자가 없습니다.")
        else:
            print(f"📋 총 {len(pending_users)}명의 대기자가 있습니다:")
            for user in pending_users:
                print(f"- ID: {user['id']} | 이름: {user['name']} | 닉네임: {user.get('nick_nm', 'N/A')} | 이메일: {user['email']}")
        return pending_users
    except Exception as e:
        print(f"❌ 사용자 조회 실패: {e}")
        return []

def approve_user(db, user_id):
    print(f"🚀 사용자 승인 시도 중 (Supabase): {user_id}")
    try:
        # 사용자 존재 확인
        user = db.get_user(user_id)
        if not user:
            print(f"❌ 에러: ID가 '{user_id}'인 사용자를 찾을 수 없습니다.")
            return False
        
        # 권한 업데이트
        query = "UPDATE users SET permission = 'approved', updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        db.execute_query(query, (user_id,), fetch=False)
        
        print(f"✅ 성공: 사용자 '{user_id}'가 승인되었습니다! 이제 로그인이 가능합니다.")
        return True
    except Exception as e:
        print(f"❌ 승인 실패: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bell 사용자 승인 툴 (Supabase)')
    parser.add_argument('--list', action='store_true', help='승인 대기 중인 사용자 목록 표시')
    parser.add_argument('--approve', type=str, help='승인할 사용자 ID')
    
    args = parser.parse_args()
    
    db = DBManager()
    
    if args.list:
        list_pending_users(db)
    elif args.approve:
        approve_user(db, args.approve)
    else:
        parser.print_help()
