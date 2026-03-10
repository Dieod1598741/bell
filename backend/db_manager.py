import os
import sys
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import threading
import time

# .env 파일 로드 (PyInstaller frozen 대응)
if getattr(sys, 'frozen', False):
    # PyInstaller 빌드 환경 (_MEIPASS는 임시 압축 해제 경로)
    base_path = getattr(sys, '_MEIPASS', os.getcwd())
    # 여러 후보 경로 확인
    env_candidates = [
        os.path.join(base_path, 'backend', '.env'),
        os.path.join(base_path, '.env'),
        os.path.join(os.path.dirname(sys.executable), '.env'), # 실행파일 옆
        os.path.join(os.getcwd(), '.env')
    ]
else:
    # 일반 파이썬 실행 환경
    base_path = os.path.dirname(os.path.abspath(__file__))
    env_candidates = [os.path.join(base_path, '.env')]

env_path = None
for candidate in env_candidates:
    if os.path.exists(candidate):
        env_path = candidate
        break

if env_path:
    print(f"[DB] Loading environment from: {env_path}")
    load_dotenv(env_path)
else:
    print(f"[DB] Warning: .env file not found in candidates")
    load_dotenv() # 시스템 환경변수라도 시도
    
# 필수 환경변수 확인
if not os.getenv("NEON_DB_HOST"):
    print("[DB] CRITICAL: NEON_DB_HOST not found in environment!")

class DBManager:
    """PostgreSQL (Supabase) 관리를 위한 싱글톤 클래스"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DBManager, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.host = os.getenv("NEON_DB_HOST")
        self.dbname = os.getenv("NEON_DB_NAME", "neondb")
        self.user = os.getenv("NEON_DB_USER", "neondb_owner")
        self.password = os.getenv("NEON_DB_PASSWORD")
        self.port = os.getenv("NEON_DB_PORT", "5432")
        
        if not self.host or not self.password:
            print(f"[DB] Error: Database credentials missing in environment (Host: {'OK' if self.host else 'Missing'})")
        
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,
                host=self.host,
                database=self.dbname,
                user=self.user,
                password=self.password,
                port=self.port,
                sslmode='require' # Neon DB 등에서 필수
            )
            print("[DB] Connection pool created successfully")
            self._initialized = True
        except Exception as e:
            print(f"[DB] Error creating connection pool: {e}")
            self.connection_pool = None

    def get_connection(self):
        """커넥션 풀에서 커넥션을 가져오며 상태를 점검합니다."""
        if not self.connection_pool:
            print("[DB] Connection pool is not initialized. Re-initializing...")
            self.__init__()
            if not self.connection_pool:
                return None
        
        try:
            conn = self.connection_pool.getconn()
            # 커넥션 생존 확인 (SELECT 1)
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            return conn
        except Exception as e:
            print(f"[DB] Connection health check failed: {e}")
            if 'conn' in locals():
                try: self.connection_pool.putconn(conn, close=True)
                except: pass
            return None

    def put_connection(self, conn, fail=False):
        if self.connection_pool:
            try:
                self.connection_pool.putconn(conn, close=fail)
            except:
                pass

    def execute_query(self, query, params=None, fetch=True, retries=3):
        """쿼리 실행 (SELECT 등). 성공 시 (결과, None), 실패 시 (None, 에러메시지) 반환.
        Neon 등의 서버리스 DB 연결 끊김을 대비해 재시도 로직을 포함합니다.
        """
        last_error = "Unknown error"
        
        for attempt in range(retries):
            conn = self.get_connection()
            if not conn:
                last_error = "데이터베이스 연결에 실패했습니다 (커넥션 획득 불가)."
                time.sleep(1)
                continue
                
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    if fetch:
                        result = cur.fetchall()
                        self.put_connection(conn)
                        return result, None
                    conn.commit()
                    self.put_connection(conn)
                    return True, None
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                # 연결 관련 에러는 재시도
                last_error = str(e)
                print(f"[DB] Connection error (attempt {attempt+1}/{retries}): {last_error}")
                self.put_connection(conn, fail=True)
                time.sleep(1)
            except Exception as e:
                # 일반적인 SQL 에러는 재시도 없이 즉시 반환
                last_error = str(e)
                print(f"[DB] SQL error: {last_error}")
                if 'conn' in locals() and conn:
                    conn.rollback()
                    self.put_connection(conn)
                return None, last_error
                
        return None, f"최대 재시도 횟수를 초과했습니다: {last_error}"

    def execute_one(self, query, params=None):
        """단일 행 결과 반환"""
        result, error = self.execute_query(query, params)
        return result[0] if result else None

    # --- User-related operations ---
    
    def get_user(self, user_id):
        """사용자 ID로 정보 조회 (대소문자 구분 없음)"""
        if not user_id: return None
        query = 'SELECT * FROM "users" WHERE LOWER("id") = LOWER(%s) AND "del_yn" = \'n\''
        return self.execute_one(query, (user_id.strip(),))

    def update_user_status(self, user_id, status):
        query = 'UPDATE "users" SET "user_status" = %s, "updated_at" = CURRENT_TIMESTAMP WHERE "id" = %s'
        return self.execute_query(query, (status, user_id), fetch=False)

    def create_user(self, user_data):
        """사용자 정보를 데이터베이스에 저장 (필드 매핑 포함)"""
        # 프론트엔드 CamelCase 필드를 DB snake_case 필드로 매핑
        mapping = {
            'userId': 'id',
            'nickNm': 'nick_nm',
            'avatarColor': 'avatar_color',
            'connectionStatus': 'connection_status',
            'userStatus': 'user_status'
        }
        
        processed_data = {}
        for k, v in user_data.items():
            db_key = mapping.get(k, k)
            if db_key == 'confirmPassword': continue # 비밀번호 확인 필드는 제외
            # 타입 힌트 에러 방지를 위해 명시적 캐스팅 또는 간단한 할당
            processed_data[str(db_key)] = v
            
        keys = list(processed_data.keys())
        columns = ', '.join([f'"{k}"' for k in keys])
        placeholders = ', '.join(['%s'] * len(keys))
        
        # 업데이트할 컬럼들 (id 제외)
        update_cols = [col for col in keys if col != 'id']
        if update_cols:
            update_stmt = ', '.join([f'"{col}" = EXCLUDED."{col}"' for col in update_cols])
            query = f"INSERT INTO users ({columns}) VALUES ({placeholders}) " \
                    f"ON CONFLICT (id) DO UPDATE SET {update_stmt}, updated_at = CURRENT_TIMESTAMP"
        else:
            query = f"INSERT INTO users ({columns}) VALUES ({placeholders}) " \
                    f"ON CONFLICT (id) DO NOTHING"
        
        print(f"[DB] Creating/Updating user: {processed_data.get('id')}")
        result, error = self.execute_query(query, tuple(processed_data[k] for k in keys), fetch=False)
        if error:
            return False, error
        return True, None

    def get_unread_count(self, user_id):
        """읽지 않은 메시지 및 알림 총 개수 반환"""
        count = 0
        try:
            # 1. 채팅 읽지 않은 개수
            chat_query = 'SELECT COUNT(*) FROM "chats" WHERE "target_user_id" = %s AND "read" = false AND "del_yn" = \'n\''
            chat_res = self.execute_one(chat_query, (user_id,))
            if chat_res: count += chat_res['count']
            
            # 2. 인박스/공지 읽지 않은 개수
            inbox_query = 'SELECT COUNT(*) FROM "inbox" WHERE "target_user_id" = %s AND "read" = false AND "del_yn" = \'n\''
            inbox_res = self.execute_one(inbox_query, (user_id,))
            if inbox_res: count += inbox_res['count']
        except Exception as e:
            print(f"[DB] Error getting unread count: {e}")
        return count
