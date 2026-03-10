"""GUI 프로세스 - 프론트엔드 빌드 결과만 서빙"""
import sys
import os
import webview
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from threading import Thread
import socket
import queue
import time
import requests
import webbrowser

# 상위 디렉토리를 경로에 추가
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sse_manager import SSEManager

# 데이터 디렉토리
DATA_DIR = Path.home() / ".bell"
DATA_DIR.mkdir(exist_ok=True)

# WebView localStorage 영구 저장 디렉토리
WEBVIEW_STORAGE_DIR = DATA_DIR / "webview_data"
WEBVIEW_STORAGE_DIR.mkdir(exist_ok=True)

# GUI 프로세스 락 파일 (중복 실행 방지)
GUI_LOCK_FILE = DATA_DIR / "gui_process.lock"

# UserInfoManager import
from user_info import UserInfoManager
from machine_id import get_hardware_uuid
from activity_monitor import ActivityMonitor
from db_manager import DBManager
from sse_manager import SSEManager

CURRENT_VERSION = "v1.1.42"

# 트레이 상태 전역 변수 (SSE 클라이언트 연결 시 즉시 동기화용)
_current_tray_status = 'offline'

def to_camel(snake_str):
    """snake_case를 camelCase로 변환"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def transform_user_data(user):
    """DB의 snake_case 사용자 데이터를 프론트엔드가 기대하는 camelCase로 매핑/보강"""
    if not user: return user
    
    # 1. 기본 snake_case -> camelCase 변환
    new_user = {}
    for k, v in user.items():
        camel_k = to_camel(k)
        new_user[camel_k] = v
        new_user[k] = v # 원본 필드 유지 (호환성)
    
    # 2. 필수 필드 하이드레이션 (Data Hydration/Resilience)
    # 하나라도 null이거나 누락되면 프론트엔드 필터링에서 탈락할 수 있음
    new_user['id'] = user.get('id') or 'unknown'
    new_user['nickNm'] = user.get('nick_nm') or user.get('name') or new_user['id']
    new_user['name'] = user.get('name') or new_user['nickNm']
    new_user['userStatus'] = user.get('user_status') or 'offline'
    new_user['connectionStatus'] = user.get('connection_status') or 'offline'
    new_user['permission'] = user.get('permission') or 'approved' # 기본적으로 노출되게 유도
    new_user['del_yn'] = user.get('del_yn') or 'n'
    new_user['avatar'] = user.get('avatar') or '/icon/icon1.svg'
    
    # 디버그: 변환된 결과 확인 (필요시 주석 해제)
    # print(f"[API] Transformed user: {new_user['id']} (perm: {new_user['permission']})")
    
    return new_user


class API:
    """프론트엔드에서 호출할 백엔드 API"""
    
    def __init__(self):
        """매니저 클래스들 초기화"""
        storage_path = str(WEBVIEW_STORAGE_DIR)
        self.user_manager = UserInfoManager(storage_path)
        self.db_manager = DBManager()
        self.sse_manager = SSEManager()
        print(f"[API] 매니저 초기화 완료 (DB/SSE 포함)")
        
        # 활동 모니터 초기화
        self.activity_monitor = None
        self.last_backend_request_time = None
        self._init_activity_monitor()
        
        # IPC (Tray Update) 설정
        self.ipc_port = os.environ.get('BELL_IPC_PORT')
        if self.ipc_port:
            print(f"[API] IPC Port detected: {self.ipc_port}")
            
        # 초기 트레이 상태 설정
        try:
            current_status = self.user_manager.get_user_status()
            user_data = self.user_manager.get_user()
            count = 0
            if user_data and user_data.get('id'):
                count = self.db_manager.get_unread_count(user_data.get('id'))
            self._send_tray_update(status=current_status, count=count)
        except:
            pass
            
        # 백그라운드 동기화 시작 (DB -> SSE/Tray)
        self._start_db_sync()
            
    def _start_db_sync(self):
        """DB 변경사항을 주기적으로 확인하여 Tray와 SSE에 전파"""
        def sync_task():
            import time
            last_checked_count = -1
            while True:
                try:
                    user_data = self.user_manager.get_user()
                    if user_data and user_data.get('id'):
                        user_id = user_data.get('id')
                        
                        # 1. 읽지 않은 총 개수 확인 (배지 업데이트용)
                        current_count = self.db_manager.get_unread_count(user_id)
                        if current_count != last_checked_count:
                            self._send_tray_update(count=current_count)
                            # 개수가 늘어났으면 알림 시도 (단일 알림은 추후 로직 보강)
                            if current_count > last_checked_count and last_checked_count != -1:
                                self._send_notification("새로운 알림", f"읽지 않은 메시지가 {current_count}개 있습니다.")
                                # SSE로도 전파하여 프론트엔드 갱신 유도
                                self.sse_manager.broadcast("DB_UPDATE", {"table": "inbox", "action": "update"})
                            
                            last_checked_count = current_count
                except Exception as e:
                    print(f"[Sync] Error: {e}")
                
                time.sleep(5)  # 5초마다 확인 (폴링)
        
        import threading
        threading.Thread(target=sync_task, daemon=True).start()

    def _send_tray_update(self, status=None, count=None):
        """메인 프로세스의 트레이 아이콘 업데이트 (SSE 브로드캐스트)"""
        try:
            payload = {"action": "update_tray"}
            if status is not None:
                payload["status"] = status
            if count is not None:
                payload["count"] = count
            # main.py SSE 리스너는 event='SYSTEM', action='update_tray' 를 기대함
            self.sse_manager.broadcast("SYSTEM", payload)
            print(f"[API] Tray update sent → {payload}")
        except Exception as e:
            print(f"[API] Tray SSE broadcast failed: {e}")

    def _send_notification(self, title, message):
        """메인 프로세스를 통한 알림 출력 (SSE 브로드캐스트)"""
        try:
            self.sse_manager.broadcast({
                'action': 'notification',
                'title': title,
                'message': message
            }, event='SYSTEM')
        except Exception as e:
            print(f"[API] Notification SSE broadcast failed: {e}")
    
    # --- System 및 Update API ---
    
    def checkUpdate(self):
        """GitHub 최신 릴리즈 확인 및 플랫폼별 다운로드 URL 추출"""
        try:
            repo_url = "https://api.github.com/repos/Dieod1598741/bell/releases/latest"
            response = requests.get(repo_url, timeout=5)
            if response.status_code == 200:
                latest_data = response.json()
                latest_version = latest_data.get('tag_name')
                has_update = latest_version != CURRENT_VERSION
                
                # 플랫폼별 자산(asset) 찾기
                target_extension = '.dmg' if sys.platform == 'darwin' else '.exe'
                download_url = latest_data.get('html_url') # 폴백: 웹페이지
                
                assets = latest_data.get('assets', [])
                for asset in assets:
                    name = asset.get('name', '').lower()
                    if name.endswith(target_extension):
                        download_url = asset.get('browser_download_url')
                        print(f"[API] 플랫폼에 맞는 자산 발견: {name}")
                        break
                
                return {
                    "success": True,
                    "hasUpdate": has_update,
                    "currentVersion": CURRENT_VERSION,
                    "latestVersion": latest_version,
                    "downloadUrl": download_url,
                    "body": latest_data.get('body')
                }
            return {"success": False, "error": f"GitHub API 오류: {response.status_code}"}
        except Exception as e:
            print(f"[API] checkUpdate 오류: {e}")
            return {"success": False, "error": str(e)}

    def openUrl(self, url):
        """시스템 브라우저로 URL 열기"""
        try:
            if url:
                webbrowser.open(url)
                return {"success": True}
            return {"success": False, "error": "URL이 없습니다."}
        except Exception as e:
            print(f"[API] openUrl 오류: {e}")
            return {"success": False, "error": str(e)}

    def downloadUpdate(self, url):
        """배경에서 업데이트 파일 다운로드"""
        try:
            if not url:
                return {"success": False, "error": "URL이 없습니다."}
            
            # 저장 경로 설정 (~/.bell/updates/)
            update_dir = DATA_DIR / "updates"
            update_dir.mkdir(exist_ok=True)
            
            filename = url.split('/')[-1]
            save_path = update_dir / filename
            
            # 다운로드 시작
            print(f"[API] 업데이트 다운로드 시작: {url}")
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            # 진행률 계산 (필요 시 SSE로 쏠 수 있음)
                            
                print(f"[API] 다운로드 완료: {save_path}")
                return {
                    "success": True, 
                    "savePath": str(save_path),
                    "filename": filename
                }
            return {"success": False, "error": f"HTTP 오류: {response.status_code}"}
        except Exception as e:
            print(f"[API] downloadUpdate 오류: {e}")
            return {"success": False, "error": str(e)}

    def runInstaller(self, file_path):
        """다운로드된 설치 파일 실행 및 앱 종료"""
        try:
            if not file_path or not os.path.exists(file_path):
                return {"success": False, "error": "파일을 찾을 수 없습니다."}
            
            print(f"[API] 설치 프로그램 실행 시도: {file_path}")
            
            # 플랫폼별 실행 방식
            if sys.platform == 'darwin':  # macOS
                # .dmg 파일 마운트 및 열기
                os.system(f"open '{file_path}'")
            elif sys.platform == 'win32':  # Windows
                # .exe 설치 파일 실행
                os.startfile(file_path)
            
            # 프로그램 종료 (사용자가 설치를 진행할 수 있도록)
            # 1초 뒤에 종료 (API 응답을 프론트가 받을 시간을 줌)
            def quit_app():
                time.sleep(1)
                print("[API] 업데이트를 위해 종료합니다.")
                os._exit(0)
            
            Thread(target=quit_app).start()
            return {"success": True}
        except Exception as e:
            print(f"[API] runInstaller 오류: {e}")
            return {"success": False, "error": str(e)}

    def _init_activity_monitor(self):
        """활동 모니터 초기화 (초기에는 시작하지 않음)"""
        self.last_backend_request_time = None
        
        def on_activity_change(is_active):
            """활동 상태 변경 시 호출"""
            try:
                user_data = self.user_manager.get_user()
                # 사용자 정보가 없으면 상태 변경하지 않음
                if not user_data or not user_data.get('id'):
                    return
                
                user_id = user_data.get('id')
                current_status = self.user_manager.get_user_status()
                
                # 현재 상태가 'offline'이 아니고, 로그인된 사용자가 있을 때만 상태 변경
                if current_status != 'offline':
                    new_status = 'online' if is_active else 'away'
                    if current_status != new_status:
                        self.user_manager.save_user_status(new_status)
                        self._send_tray_update(status=new_status)
                        print(f"[ActivityMonitor] 상태 변경: {current_status} -> {new_status} (user_id={user_id})")
            except Exception as e:
                print(f"[ActivityMonitor] 상태 변경 처리 실패: {e}")
        
        def on_backend_request():
            """백엔드 요청이 있었는지 확인 (마우스 이벤트를 제어 못할 때 사용)"""
            if self.last_backend_request_time is None:
                return False
            from datetime import datetime
            elapsed = (datetime.now() - self.last_backend_request_time).total_seconds() / 60
            return elapsed < 5  # 5분 이내에 요청이 있었으면 True
        
        try:
            self.activity_monitor = ActivityMonitor(
                on_activity_change=on_activity_change,
                on_backend_request=on_backend_request
            )
            # 초기에는 시작하지 않음 (로그인 시 시작)
            print("[API] 활동 모니터 초기화 완료 (로그인 시 시작)")
        except Exception as e:
            print(f"[API] 활동 모니터 초기화 실패: {e}")
    
    def _update_backend_request_time(self):
        """백엔드 요청 시간 업데이트 (마우스 이벤트를 제어 못할 때 사용)"""
        if self.activity_monitor and not self.activity_monitor.mouse_listener:
            from datetime import datetime
            self.last_backend_request_time = datetime.now()
            if self.activity_monitor:
                self.activity_monitor.update_backend_request_time()
    
    def getActivityStatus(self):
        """활동 상태 조회"""
        try:
            self._update_backend_request_time()
            
            if self.activity_monitor:
                is_active = self.activity_monitor.get_is_active()
                last_activity = self.activity_monitor.get_last_activity_time()
                return {
                    "success": True,
                    "data": {
                        "is_active": is_active,
                        "last_activity_time": last_activity.isoformat() if last_activity else None
                    }
                }
            else:
                return {"success": False, "error": "활동 모니터가 초기화되지 않았습니다"}
        except Exception as e:
            print(f"[API] getActivityStatus 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def getHardwareId(self):
        """하드웨어 ID 조회"""
        try:
            self._update_backend_request_time()
            hardware_id = get_hardware_uuid()
            if hardware_id:
                return {"success": True, "data": hardware_id}
            else:
                return {"success": False, "error": "하드웨어 ID를 가져올 수 없습니다"}
        except Exception as e:
            print(f"[API] getHardwareId 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def getUserInfo(self):
        """사용자 정보 조회 (DB 우선, 로컬 보완)"""
        try:
            self._update_backend_request_time()
            user_data = self.user_manager.get_user()
            if not user_data:
                return {"success": False, "data": None, "message": "사용자 정보 없음 (로컬)"}
            
            # DB에서 최신 정보 가져오기
            db_user = self.db_manager.get_user(user_data.get('id'))
            if db_user:
                # DB 정보가 최신이므로 로컬 동기화
                self.user_manager.save_user(db_user)
                return {"success": True, "data": db_user, "db_synced": True}
            
            # DB에 없는데 로컬엔 있는 경우 (동기화 누락 상태)
            print(f"[API] Warning: User {user_data.get('id')} found locally but not in DB.")
            return {
                "success": True, 
                "data": user_data, 
                "db_synced": False, 
                "message": "데이터베이스와 동기화되지 않은 계정입니다. 다시 가입하거나 관리자에게 문의하세요."
            }
        except Exception as e:
            print(f"[API] getUserInfo 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def getUserById(self, user_id):
        """특정 사용자 정보 조회 (로그인 등에서 사용)"""
        try:
            self._update_backend_request_time()
            if not user_id:
                return {"success": False, "message": "사용자 ID가 없습니다."}
            
            db_user = self.db_manager.get_user(user_id)
            if db_user:
                return {"success": True, "data": transform_user_data(db_user)}
            else:
                return {"success": False, "message": "사용자를 찾을 수 없습니다."}
        except Exception as e:
            print(f"[API] getUserById 오류: {e}")
            return {"success": False, "error": str(e)}

    def saveUserInfo(self, user_data):
        """사용자 정보 저장 (로컬 + DB)"""
        try:
            if not user_data:
                return {"success": False, "error": "user_data가 필요합니다"}
            
            print(f"[API] saveUserInfo 호출: {user_data.get('id')}")
            
            # 1. 로컬 저장
            self.user_manager.save_user(user_data)
            
            # 2. DB 저장
            db_success, db_error = self.db_manager.create_user(user_data)
            
            if not db_success:
                print(f"[API] DB 저장 실패 에러 상세: {db_error}")
                return {"success": False, "error": f"데이터베이스 저장 실패: {db_error}"}
            
            # 3. SSE 알림
            self.sse_manager.publish_update("users", "upsert", user_data)
            
            return {"success": True, "message": "저장 및 동기화 완료"}
        except Exception as e:
            print(f"[API] saveUserInfo 오류: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def updateUserInfo(self, user_data):
        """saveUserInfo의 별칭 (프론트엔드 호환용)"""
        return self.saveUserInfo(user_data)

    # --- 실시간 채팅 및 알림 API ---

    def sendChatMessage(self, sender_id, target_id, content):
        """채팅 메시지 전송 및 SSE 전파"""
        try:
            query = "INSERT INTO chats (sender_user_id, target_user_id, content) VALUES (%s, %s, %s) RETURNING *"
            result, error = self.db_manager.execute_query(query, (sender_id, target_id, content))
            if result:
                msg = result[0]
                # 타겟과 본인에게 알림
                self.sse_manager.broadcast("NEW_CHAT", msg)
                return {"success": True, "data": msg}
            return {"success": False, "error": f"메시지 저장 실패: {error}"}
        except Exception as e:
            print(f"[API] sendChatMessage 오류: {e}")
            return {"success": False, "error": str(e)}

    def sendAnnouncement(self, user_ids, message, sender_id='admin'):
        """공지/알림 발송 (다수 사용자)"""
        try:
            results = []
            for user_id in user_ids:
                query = "INSERT INTO announcements (sender_user_id, target_user_id, message) VALUES (%s, %s, %s) RETURNING *"
                res, error = self.db_manager.execute_query(query, (sender_id, user_id, message))
                if res:
                    results.append(res[0])
            
            # 전체 또는 유관자에게 브로드캐스트
            self.sse_manager.broadcast("NEW_ANNOUNCEMENT", {"message": message, "count": len(results)})
            return {"success": True, "data": results}
        except Exception as e:
            print(f"[API] sendAnnouncement 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def getMessages(self, user_id, current_user_id, limit_val=50):
        """채팅 메시지 로드 (PostgreSQL)"""
        try:
            query = 'SELECT * FROM "chats" WHERE (("sender_user_id" = %s AND "target_user_id" = %s) OR ("sender_user_id" = %s AND "target_user_id" = %s)) AND "del_yn" = \'n\' ORDER BY "timestamp" ASC LIMIT %s'
            result, error = self.db_manager.execute_query(query, (user_id, current_user_id, current_user_id, user_id, limit_val))
            if error:
                print(f"[API] getMessages DB 오류: {error}")
                return {"success": False, "error": f"메시지 조회 실패: {error}"}
            return {"success": True, "data": result or []}
        except Exception as e:
            print(f"[API] getMessages 예외 오류: {e}")
            return {"success": False, "error": str(e)}

    def getInbox(self, user_id, limit_val=50):
        """인박스 알림 로드"""
        try:
            query = 'SELECT * FROM "inbox" WHERE "target_user_id" = %s AND "del_yn" = \'n\' ORDER BY "timestamp" DESC LIMIT %s'
            result, error = self.db_manager.execute_query(query, (user_id, limit_val))
            if error:
                return {"success": False, "error": f"인박스 조회 실패: {error}"}
            return {"success": True, "data": result or []}
        except Exception as e:
            print(f"[API] getInbox 오류: {e}")
            return {"success": False, "error": str(e)}

    def markMessageRead(self, message_id, msg_type='chat'):
        """메시지 읽음 처리"""
        try:
            table = 'chats' if msg_type == 'chat' else 'inbox'
            query = f"UPDATE {table} SET read = TRUE WHERE id = %s"
            self.db_manager.execute_query(query, (message_id,), fetch=False)
            return {"success": True}
        except Exception as e:
            print(f"[API] markMessageRead 오류: {e}")
            return {"success": False, "error": str(e)}

    def getAllUsers(self):
        """전체 사용자 목록 (관리자용 또는 목록용)"""
        try:
            query = 'SELECT "id", "name", "nick_nm", "avatar", "user_status", "connection_status", "permission", "del_yn" FROM "users" WHERE "del_yn" = \'n\' ORDER BY "nick_nm" ASC'
            result, error = self.db_manager.execute_query(query)
            if error:
                print(f"[API] getAllUsers DB 오류: {error}")
                return {"success": False, "error": f"사용자 목록 조회 실패: {error}"}
            
            raw_count = len(result) if result else 0
            print(f"[API] getAllUsers Raw Record Count: {raw_count}")
            
            # 모든 유저 정보 변환
            transformed = [transform_user_data(u) for u in (result or [])]
            print(f"[API] getAllUsers Transformed Count: {len(transformed)}")
            
            return {"success": True, "data": transformed}
        except Exception as e:
            print(f"[API] getAllUsers 예외 오류: {e}")
            return {"success": False, "error": str(e)}

    def getUserStatus(self):
        """사용자 상태 조회"""
        try:
            status = self.user_manager.get_user_status()
            if status:
                return {"success": True, "data": status}
            else:
                return {"success": False, "data": None, "message": "상태 정보 없음"}
        except Exception as e:
            print(f"[API] getUserStatus 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def saveUserStatus(self, status):
        """사용자 상태 저장"""
        global _current_tray_status
        try:
            if not status:
                return {"success": False, "error": "status가 필요합니다"}
            
            # 1. 로컬 저장
            result = self.user_manager.save_user_status(status)
            
            # 2. DB 저장
            user_data = self.user_manager.get_user()
            if user_data and user_data.get('id'):
                self.db_manager.update_user_status(user_data.get('id'), status)
                print(f"[API] DB 상태 업데이트 완료: {user_data.get('id')} -> {status}")
            
            # 3. 모듈 레벨 상태 업데이트 (SSE 신규 연결 시 동기화용)
            _current_tray_status = status
            
            # 4. 트레이 아이콘 즉시 반영
            self._send_tray_update(status=status)
            
            if result:
                return {"success": True, "message": "상태 저장 완료"}
            else:
                return {"success": False, "error": "상태 저장 실패"}
        except Exception as e:
            print(f"[API] saveUserStatus 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def deleteUserStatus(self):
        """사용자 상태 삭제"""
        try:
            result = self.user_manager.delete_user_status()
            if result:
                return {"success": True, "message": "상태 삭제 완료"}
            else:
                return {"success": False, "error": "상태 삭제 실패"}
        except Exception as e:
            print(f"[API] deleteUserStatus 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def getLoginSettings(self):
        """하드웨어 ID별 로그인 설정 조회"""
        try:
            self._update_backend_request_time()
            hardware_id = get_hardware_uuid()
            if not hardware_id:
                return {"success": False, "error": "하드웨어 ID를 가져올 수 없습니다"}
            
            settings = self.user_manager.get_login_settings(hardware_id)
            if settings:
                return {"success": True, "data": settings}
            else:
                return {"success": False, "data": None, "message": "로그인 설정 없음"}
        except Exception as e:
            print(f"[API] getLoginSettings 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def saveLoginSettings(self, settings):
        """하드웨어 ID별 로그인 설정 저장"""
        try:
            hardware_id = get_hardware_uuid()
            if not hardware_id:
                return {"success": False, "error": "하드웨어 ID를 가져올 수 없습니다"}
            
            if not settings:
                return {"success": False, "error": "settings가 필요합니다"}
            
            result = self.user_manager.save_login_settings(hardware_id, settings)
            if result:
                return {"success": True, "message": "로그인 설정 저장 완료"}
            else:
                return {"success": False, "error": "로그인 설정 저장 실패"}
        except Exception as e:
            print(f"[API] saveLoginSettings 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def deleteLoginSettings(self):
        """하드웨어 ID별 로그인 설정 삭제"""
        try:
            hardware_id = get_hardware_uuid()
            if not hardware_id:
                return {"success": False, "error": "하드웨어 ID를 가져올 수 없습니다"}
            
            result = self.user_manager.delete_login_settings(hardware_id)
            if result:
                return {"success": True, "message": "로그인 설정 삭제 완료"}
            else:
                return {"success": False, "error": "로그인 설정 삭제 실패"}
        except Exception as e:
            print(f"[API] deleteLoginSettings 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def showNotification(self, title, message, notification_type='info', sender_name=None):
        """시스템 알림 표시 (macOS/Windows 크로스플랫폼)"""
        self._update_backend_request_time()
        import platform
        system = platform.system()
        
        # ── 아이콘 경로 결정 ───────────────────────────────────
        def find_icon(ext):
            """플랫폼 별 아이콘 파일 탐색"""
            candidates = [f'bell_icon{ext}', f'icon{ext}']
            for name in candidates:
                if getattr(sys, 'frozen', False):
                    for sub in ['.', 'tray', 'backend/tray']:
                        p = os.path.join(sys._MEIPASS, sub, name)
                        if os.path.exists(p):
                            return p
                else:
                    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    p = os.path.join(backend_dir, 'tray', name)
                    if os.path.exists(p):
                        return p
            return None
        
        icon_path = find_icon('.ico') if system == 'Windows' else find_icon('.png')
        print(f"[API] 알림 전송: {title} – {message} (icon={icon_path})")
        
        # ── macOS: osascript 직접 사용 (plyer보다 안정적) ─────
        if system == 'Darwin':
            try:
                import subprocess
                # 특수문자 이스케이프
                safe_title   = title.replace('"', '\\"')
                safe_message = message.replace('"', '\\"')
                script = f'display notification "{safe_message}" with title "{safe_title}"'
                subprocess.run(['osascript', '-e', script], check=False, timeout=5)
                return {"success": True}
            except Exception as e:
                print(f"[API] osascript 알림 실패: {e}, plyer로 재시도")
        
        # ── Windows / 폴백: plyer ─────────────────────────────
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                app_name='Bell',
                app_icon=icon_path,   # None 안전 (plyer가 기본값 사용)
                timeout=10,
            )
            return {"success": True}
        except Exception as e:
            print(f"[API] 알림 표시 오류: {e}")
            import traceback; traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    # ─── 자동 업데이트 ────────────────────────────────────────────
    
    def checkUpdate(self):
        """GitHub Releases API로 최신 버전 확인"""
        try:
            import platform
            REPO = "Dieod1598741/bell"
            API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
            
            print(f"[API] 업데이트 확인 중... 현재 버전: {CURRENT_VERSION}")
            resp = requests.get(API_URL, timeout=10,
                                headers={"Accept": "application/vnd.github+json",
                                         "User-Agent": "Bell-App"})
            if resp.status_code != 200:
                return {"success": False, "error": f"GitHub API 응답 오류: {resp.status_code}"}
            
            data = resp.json()
            latest_version = data.get("tag_name", "")
            release_notes = data.get("body", "")
            
            # 버전 비교 (v1.2.3 형식)
            def parse_ver(v):
                return tuple(int(x) for x in v.lstrip("v").split("."))
            
            has_update = parse_ver(latest_version) > parse_ver(CURRENT_VERSION)
            print(f"[API] 최신 버전: {latest_version}, 업데이트 필요: {has_update}")
            
            if not has_update:
                return {"success": True, "hasUpdate": False,
                        "currentVersion": CURRENT_VERSION, "latestVersion": latest_version}
            
            # 플랫폼에 맞는 에셋 URL 추출
            assets = data.get("assets", [])
            system = platform.system()
            download_url = ""
            for asset in assets:
                name = asset.get("name", "").lower()
                if system == "Darwin" and name.endswith(".dmg"):
                    download_url = asset.get("browser_download_url", "")
                    break
                elif system == "Windows" and name.endswith(".exe"):
                    download_url = asset.get("browser_download_url", "")
                    break
            
            # 에셋이 없으면 release HTML URL 반환
            if not download_url:
                download_url = data.get("html_url", "")
            
            return {
                "success": True,
                "hasUpdate": True,
                "currentVersion": CURRENT_VERSION,
                "latestVersion": latest_version,
                "downloadUrl": download_url,
                "releaseNotes": release_notes
            }
        except Exception as e:
            print(f"[API] 업데이트 확인 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def downloadUpdate(self, url):
        """업데이트 파일 다운로드 (스트리밍)"""
        try:
            import platform
            
            update_dir = DATA_DIR / "update"
            update_dir.mkdir(exist_ok=True)
            
            system = platform.system()
            ext = ".dmg" if system == "Darwin" else ".exe"
            save_path = str(update_dir / f"Bell_update{ext}")
            
            print(f"[API] 업데이트 다운로드 시작: {url} → {save_path}")
            
            resp = requests.get(url, stream=True, timeout=120)
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = int(downloaded / total * 100)
                            # SSE로 진행률 전송 (프론트엔드 UpdateAlert에서 수신 가능)
                            sse = SSEManager()
                            sse.broadcast({
                                "type": "UPDATE_PROGRESS",
                                "percent": pct,
                                "downloaded": downloaded,
                                "total": total
                            })
            
            print(f"[API] 다운로드 완료: {save_path}")
            return {"success": True, "savePath": save_path}
        except Exception as e:
            print(f"[API] 다운로드 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def runInstaller(self, file_path):
        """설치 프로그램 실행 후 앱 종료 → 자동 재시작 (macOS/Windows)"""
        try:
            import platform
            import subprocess
            import signal
            import tempfile
            import threading

            system = platform.system()
            print(f"[API] 자동 업데이트 설치 시작: {file_path} (OS: {system})")

            if system == "Darwin":
                # ── macOS 자동 업데이트 ────────────────────────────────
                # 1. 독립 쉘 스크립트 작성 (Bell 종료 후에도 계속 실행)
                dst_app = "/Applications/Bell.app"
                mount_pt = "/Volumes/Bell_Update"
                
                script = f"""#!/bin/bash
sleep 2
hdiutil detach "{mount_pt}" 2>/dev/null
hdiutil attach "{file_path}" -mountpoint "{mount_pt}" -nobrowse -quiet
if [ -d "{mount_pt}/Bell.app" ]; then
    rm -rf "{dst_app}"
    cp -R "{mount_pt}/Bell.app" "{dst_app}"
    hdiutil detach "{mount_pt}" -quiet 2>/dev/null
    rm -f "{file_path}"
    open "{dst_app}"
fi
rm -f "$0"
"""
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh',
                                                 delete=False, dir='/tmp') as f:
                    f.write(script)
                    script_path = f.name

                os.chmod(script_path, 0o755)
                # 독립 프로세스로 실행 (Bell이 종료돼도 계속 실행됨)
                subprocess.Popen(['/bin/bash', script_path],
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL,
                                  close_fds=True,
                                  start_new_session=True)

                # 2. 부모 프로세스(main.py 트레이)도 종료 → 새 Bell이 단독으로 실행
                def quit_all():
                    try:
                        os.kill(os.getppid(), signal.SIGTERM)  # main.py 종료
                    except Exception:
                        pass
                    os._exit(0)  # gui_process 자신도 종료

                threading.Timer(1.0, quit_all).start()
                return {"success": True, "message": "업데이트 설치 중... 2초 후 자동 재시작됩니다."}

            elif system == "Windows":
                # ── Windows 자동 업데이트 ──────────────────────────────
                # 현재 Bell.exe 경로
                current_exe = sys.executable if getattr(sys, 'frozen', False) else sys.executable
                
                bat = f"""@echo off
timeout /t 2 /nobreak >nul
taskkill /IM Bell.exe /F >nul 2>&1
timeout /t 1 /nobreak >nul
copy /Y "{file_path}" "{current_exe}"
del /F /Q "{file_path}"
start "" "{current_exe}"
del "%~f0"
"""
                bat_path = os.path.join(tempfile.gettempdir(), 'bell_update.bat')
                with open(bat_path, 'w') as f:
                    f.write(bat)

                subprocess.Popen(
                    [bat_path],
                    creationflags=getattr(subprocess, 'CREATE_NEW_CONSOLE', 0) |
                                  getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0),
                    close_fds=True
                )
                threading.Timer(1.0, lambda: os._exit(0)).start()
                return {"success": True, "message": "업데이트 설치 중... 자동 재시작됩니다."}

            else:
                return {"success": False, "error": f"지원하지 않는 OS: {system}"}

        except Exception as e:
            print(f"[API] 설치 오류: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def openUrl(self, url):
        """외부 브라우저로 URL 열기"""
        try:
            webbrowser.open(url)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}



class SimpleWebHandler(SimpleHTTPRequestHandler):
    """간단한 정적 파일 서버"""
    
    def __init__(self, *args, web_dir=None, **kwargs):
        self.web_dir = web_dir
        self.sse_manager = SSEManager()
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """GET 요청 처리 - SSE 지원 추가"""
        if self.path == '/events':
            # SSE 스트림 시작
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # 클라이언트 큐 생성 및 등록
            q = self.sse_manager.add_client()
            try:
                # 초기 연결 성공 알림
                self.wfile.write(b"data: {\"status\": \"connected\"}\n\n")
                self.wfile.flush()
                
                # 현재 트레이 상태를 즉시 전송 (SSE 연결 타이밍 경쟁 조건 해소)
                import json as _json
                _sync_payload = _json.dumps({"action": "update_tray", "status": _current_tray_status})
                self.wfile.write(f"event: SYSTEM\ndata: {_sync_payload}\n\n".encode('utf-8'))
                self.wfile.flush()
                
                while True:
                    try:
                        # 큐에서 메시지 대기 (타임아웃을 두어 연결 상태 확인)
                        message = q.get(timeout=20)
                        self.wfile.write(message.encode('utf-8'))
                        self.wfile.flush()
                    except queue.Empty:
                        # 주기적인 Keep-alive 핑
                        self.wfile.write(b": keep-alive\n\n")
                        self.wfile.flush()
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                pass
            finally:
                self.sse_manager.remove_client(q)
            return

        # 기존 정적 파일 서빙 로직
        return super().do_GET()
    
    def translate_path(self, path):
        """경로 변환 - SPA 라우팅 지원"""
        # 쿼리 스트링 제거
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        
        # 루트는 index.html
        if path == '/' or path == '':
            path = 'index.html'
        else:
            path = path.lstrip('/')
        
        # 전체 경로
        full_path = os.path.join(self.web_dir, path)
        full_path = os.path.normpath(full_path)
        
        # 보안: 디렉토리 밖으로 나가는 경로 방지
        web_dir_norm = os.path.normpath(self.web_dir)
        if not full_path.startswith(web_dir_norm):
            return os.path.join(web_dir_norm, 'index.html')
        
        # 파일이 존재하면 반환
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return full_path
        
        # 디렉토리인 경우 index.html 확인
        if os.path.isdir(full_path):
            index_path = os.path.join(full_path, 'index.html')
            if os.path.exists(index_path):
                return index_path
        
        # 파일이 없으면 index.html로 폴백 (SPA 라우팅)
        return os.path.join(web_dir_norm, 'index.html')
    
    def log_message(self, format, *args):
        """로그 메시지 억제 (선택사항)"""
        # 필요시 주석 해제
        # print(f"[WebServer] {format % args}")
        pass


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """멀티스레딩 지원 HTTP 서버 (SSE용)"""
    daemon_threads = True

class SimpleWebServer:
    """간단한 웹 서버"""
    
    def __init__(self, web_dir):
        self.web_dir = os.path.abspath(web_dir)
        self.server = None
        self.thread = None
        self.port = None
    
    def _find_free_port(self):
        """사용 가능한 포트 찾기"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
    
    def start(self):
        """서버 시작"""
        self.port = self._find_free_port()
        
        def handler_factory(web_dir):
            def create_handler(*args, **kwargs):
                return SimpleWebHandler(*args, web_dir=web_dir, **kwargs)
            return create_handler
        
        self.server = ThreadingHTTPServer(
            ('localhost', self.port),
            handler_factory(self.web_dir)
        )
        
        def run_server():
            self.server.serve_forever()
        
        self.thread = Thread(target=run_server, daemon=True)
        self.thread.start()
        
        url = f"http://localhost:{self.port}"
        print(f"BELL_PORT:{self.port}", flush=True)
        print(f"[WebServer] 서버 시작: {url}")
        return url
    
    def stop(self):
        """서버 중지"""
        if self.server:
            self.server.shutdown()
            print(f"[WebServer] 서버 중지됨")


def run_gui():
    """GUI 실행"""
    # 중복 실행 방지: 환경 변수 체크
    if os.environ.get('BELL_GUI_MODE') != '1':
        # GUI 전용 모드가 아니면 실행하지 않음 (무한 루프 방지)
        print("[GUI] BELL_GUI_MODE 환경 변수가 설정되지 않았습니다. 실행을 중단합니다.")
        return
    
    # macOS에서 GUI 프로세스는 Dock에 표시되어야 함 (창이 떠야 하므로)
    # 메인 프로세스는 시스템 트레이에만 표시하고, GUI 프로세스는 Dock에 표시
    if sys.platform == 'darwin':
        try:
            from AppKit import NSApp, NSApplicationActivationPolicyRegular
            # GUI 프로세스는 Dock에 표시 (Regular policy)
            NSApp.setActivationPolicy_(NSApplicationActivationPolicyRegular)
            print("[GUI] GUI 프로세스가 Dock에 표시됩니다")
        except Exception:
            # 실패해도 계속 진행 (기본값이 Dock에 표시)
            pass
    
    # 중복 실행 방지: 락 파일 체크
    lock_file_path = str(GUI_LOCK_FILE)
    if os.path.exists(lock_file_path):
        try:
            # 락 파일에서 PID 읽기
            with open(lock_file_path, 'r') as f:
                pid = int(f.read().strip())
            
            # 해당 PID의 프로세스가 실행 중인지 확인
            try:
                os.kill(pid, 0)  # 프로세스가 존재하면 에러 없음
                print(f"[GUI] 이미 GUI 프로세스가 실행 중입니다 (PID: {pid}). 중복 실행을 방지합니다.")
                return
            except OSError:
                # 프로세스가 존재하지 않으면 락 파일 삭제
                print(f"[GUI] 이전 프로세스가 종료되었습니다. 락 파일을 삭제합니다.")
                os.unlink(lock_file_path)
        except Exception as e:
            print(f"[GUI] 락 파일 확인 오류: {e}. 락 파일을 삭제합니다.")
            try:
                os.unlink(lock_file_path)
            except:
                pass
    
    # 락 파일 생성 (현재 PID 저장)
    try:
        with open(lock_file_path, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        print(f"[GUI] 락 파일 생성 오류: {e}")
    
    # 종료 시 락 파일 삭제를 위한 핸들러 등록
    import atexit
    def cleanup_lock():
        try:
            if os.path.exists(lock_file_path):
                os.unlink(lock_file_path)
        except:
            pass
    atexit.register(cleanup_lock)
    
    # PyInstaller로 빌드된 경우 경로 처리
    if getattr(sys, 'frozen', False):
        # PyInstaller로 빌드된 경우: sys._MEIPASS에서 파일 찾기
        base_path = sys._MEIPASS
        web_dir = os.path.join(base_path, 'backend', 'gui', 'web')
    else:
        # 일반 실행: 프로젝트 루트 찾기
        current_file = os.path.abspath(__file__)
        # backend/gui/gui_process.py -> backend -> 프로젝트 루트
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        web_dir = os.path.join(project_root, 'backend', 'gui', 'web')
    
    # 프론트엔드 빌드 디렉토리 찾기
    # 1. backend/gui/web (기존)
    # 2. frontend/dist (새로운)
    possible_dirs = [
        web_dir,
        os.path.join(os.path.dirname(web_dir), '..', 'frontend', 'dist') if not getattr(sys, 'frozen', False) else None,
    ]
    possible_dirs = [d for d in possible_dirs if d is not None]
    
    found_web_dir = None
    for dir_path in possible_dirs:
        index_path = os.path.join(dir_path, 'index.html')
        if os.path.exists(index_path):
            found_web_dir = dir_path
            break
    
    if not found_web_dir:
        print(f"[GUI] ❌ 웹 디렉토리를 찾을 수 없습니다.")
        print(f"[GUI] 다음 경로 중 하나에 index.html이 있어야 합니다:")
        for dir_path in possible_dirs:
            print(f"  - {dir_path}")
        print(f"[GUI] 프론트엔드를 먼저 빌드해주세요: cd frontend && npm run build")
        return
    
    print(f"[GUI] 웹 디렉토리: {found_web_dir}")
    
    # 웹 서버 시작
    web_server = SimpleWebServer(web_dir=found_web_dir)
    try:
        url = web_server.start()
    except Exception as e:
        print(f"[GUI] 웹 서버 시작 실패: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # webview 창 생성
    print(f"[GUI] 창 생성 중...")
    
    # API 인스턴스 생성
    api = API()
    
    # 참고: pywebview는 create_window()에서 icon 파라미터를 지원하지 않습니다.
    # macOS에서 창 아이콘을 설정하려면 앱을 번들로 패키징할 때 .icns 파일을 포함해야 합니다.
    window = webview.create_window(
        'Bell - 알람 시스템',
        url=url,
        width=450,
        height=800,
        resizable=True,
        js_api=api
    )
    
    print(f"[GUI] 창 생성 완료")
    
    # WebView localStorage 영구 저장 경로 설정
    storage_path = str(WEBVIEW_STORAGE_DIR)
    print(f"[GUI] ========================================")
    print(f"[GUI] WebView localStorage 저장소 정보")
    print(f"[GUI] ========================================")
    print(f"[GUI] 저장소 경로: {storage_path}")
    print(f"[GUI] 경로 존재 여부: {os.path.exists(storage_path)}")
    
    # 저장소 디렉토리 내용 확인 (있는 경우)
    if os.path.exists(storage_path):
        try:
            files = os.listdir(storage_path)
            if files:
                print(f"[GUI] 저장소 내 파일/폴더 수: {len(files)}")
                print(f"[GUI] 저장소 내용:")
                for item in files[:10]:  # 최대 10개만 표시
                    item_path = os.path.join(storage_path, item)
                    item_type = "디렉토리" if os.path.isdir(item_path) else "파일"
                    item_size = ""
                    if os.path.isfile(item_path):
                        size = os.path.getsize(item_path)
                        if size < 1024:
                            item_size = f" ({size}B)"
                        elif size < 1024 * 1024:
                            item_size = f" ({size // 1024}KB)"
                        else:
                            item_size = f" ({size // (1024 * 1024)}MB)"
                    print(f"[GUI]   - {item} ({item_type}){item_size}")
                if len(files) > 10:
                    print(f"[GUI]   ... 외 {len(files) - 10}개 항목")
            else:
                print(f"[GUI] 저장소가 비어있습니다.")
        except Exception as e:
            print(f"[GUI] 저장소 내용 확인 실패: {e}")
    else:
        print(f"[GUI] 저장소 디렉토리가 아직 생성되지 않았습니다.")
    print(f"[GUI] ========================================")
    
    # macOS에서 GUI 프로세스는 Dock에 표시되어야 함
    # webview.start() 후에도 다시 설정 (pywebview가 NSApp을 초기화할 수 있음)
    if sys.platform == 'darwin':
        def ensure_dock_visible():
            """GUI 프로세스가 Dock에 표시되도록 보장"""
            try:
                from AppKit import NSApp, NSApplicationActivationPolicyRegular
                NSApp.setActivationPolicy_(NSApplicationActivationPolicyRegular)
            except Exception:
                pass
        
        import threading
        def ensure_after_webview_start():
            import time
            time.sleep(0.3)  # webview가 초기화될 때까지 대기
            ensure_dock_visible()
        threading.Thread(target=ensure_after_webview_start, daemon=True).start()
    
    # webview 시작 (storage_path로 localStorage 영구 저장)
    try:
        # pywebview 버전에 따라 storage_path 파라미터 지원 여부가 다를 수 있음
        # TypeError가 발생하면 기본 동작 사용
        try:
            webview.start(debug=False, storage_path=storage_path)
            print(f"[GUI] ✅ storage_path 설정 완료: {storage_path}")
        except TypeError:
            # storage_path 파라미터를 지원하지 않는 버전인 경우
            print(f"[GUI] ⚠️ storage_path 미지원, 기본 localStorage 사용")
            print(f"[GUI] ⚠️ localStorage는 임시 디렉토리에 저장될 수 있습니다")
            webview.start(debug=False)
    except KeyboardInterrupt:
        web_server.stop()
    except SystemExit:
        web_server.stop()
    except Exception as e:
        print(f"[GUI] 오류: {e}")
        import traceback
        traceback.print_exc()
        web_server.stop()
    finally:
        # 락 파일 삭제
        try:
            lock_file_path = str(GUI_LOCK_FILE)
            if os.path.exists(lock_file_path):
                os.unlink(lock_file_path)
        except:
            pass


if __name__ == '__main__':
    run_gui()
