"""메인 진입점 - 트레이 초기화 및 GUI 실행"""
import sys
import os
import subprocess

# macOS 시스템 메시지 억제
if sys.platform == 'darwin':
    os.environ['PYTHONUNBUFFERED'] = '1'
    import warnings
    warnings.filterwarnings('ignore', category=RuntimeWarning)

# backend 폴더를 Python 경로에 추가
# PyInstaller로 빌드된 경우 경로 처리
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # PyInstaller로 빌드된 경우
    # sys._MEIPASS는 임시 추출 디렉토리
    backend_dir = getattr(sys, '_MEIPASS')
    # backend 모듈들이 sys._MEIPASS에 직접 있거나 backend/ 하위에 있을 수 있음
    if os.path.exists(os.path.join(backend_dir, 'backend')):
        backend_dir = os.path.join(backend_dir, 'backend')
else:
    # 일반 실행
    backend_dir = os.path.dirname(os.path.abspath(__file__))

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from platform_detector import PlatformDetector
from tray import TrayManager
from machine_id import get_hardware_uuid
from user_info import UserInfoManager


class BellApp:
    """Bell 애플리케이션 메인 클래스"""
    
    def __init__(self, machine_id=None):
        self.gui_process = None  # GUI 프로세스 저장
        self._gui_thread_running = False  # GUI 스레드 실행 상태
        # machine_id를 파라미터로 받거나, 없으면 가져오기
        self.machine_id = machine_id or get_hardware_uuid()
        
        # UserInfoManager 초기화 (quit 시 사용)
        from pathlib import Path
        data_dir = Path.home() / ".bell" / "webview_data"
        self.user_manager = UserInfoManager(str(data_dir))
        
        # 저장된 사용자 상태 읽기 (트레이 초기 상태 복원)
        saved_status = 'offline'
        try:
            user_data = self.user_manager.get_user()
            if user_data and user_data.get('id'):
                raw_status = self.user_manager.get_user_status()
                # offline 저장 상태라도 restart 시엔 online으로 복원
                if raw_status in ('online', 'away', 'busy'):
                    saved_status = raw_status
                else:
                    saved_status = 'online'  # 기본 복원 상태
        except Exception:
            pass
        
        # 트레이 관리자 초기화 (machine_id, app_version 전달)
        from gui.gui_process import CURRENT_VERSION  # type: ignore
        self.tray_manager = TrayManager(
            on_show_window=self.show_window,
            on_quit=self.quit,
            machine_id=self.machine_id,
            app_version=CURRENT_VERSION,
            initial_status=saved_status
        )
        
        # SSE 리스너 상태
        self.sse_thread = None
        
    def _start_sse_listener(self, port):
        """GUI 프로세스의 SSE 채널을 구독하여 트레이/알림 명령 수신"""
        import urllib.request
        import json
        import threading
        import time

        # 포트를 공유 참조로 관리 (GUI 재시작 시 업데이트 가능)
        self._sse_port = port

        def listen():
            print(f"[SSE-IPC] Connecting to http://localhost:{self._sse_port}/events...")
            consecutive_fails = 0

            while True:  # 무한 재시도 (앱 종료 시 daemon thread라 자동 종료)
                url = f"http://localhost:{self._sse_port}/events"
                try:
                    req = urllib.request.Request(url)
                    with urllib.request.urlopen(req) as response:
                        print("[SSE-IPC] Connected successfully.")
                        consecutive_fails = 0  # 성공 시 실패 카운트 리셋
                        current_event = None
                        for line in response:
                            line = line.decode('utf-8').strip()
                            if not line:
                                current_event = None
                                continue

                            if line.startswith("event:"):
                                current_event = line.replace("event:", "").strip()
                            elif line.startswith("data:"):
                                data_str = line.replace("data:", "").strip()
                                try:
                                    command = json.loads(data_str)
                                    # SYSTEM 이벤트 혹은 트레이 관련 액션 처리
                                    if current_event == 'SYSTEM' or 'action' in command:
                                        action = command.get('action')
                                        if action == 'update_tray':
                                            self.tray_manager.update_icon(
                                                status=command.get('status'),
                                                count=command.get('count')
                                            )
                                        elif action == 'notification':
                                            if hasattr(self.tray_manager._impl, 'show_notification'):
                                                self.tray_manager._impl.show_notification(
                                                    command.get('title'),
                                                    command.get('message')
                                                )
                                except Exception:
                                    pass
                except Exception as e:
                    consecutive_fails += 1
                    wait = min(consecutive_fails, 5)  # 최대 5초 대기
                    print(f"[SSE-IPC] Connection lost: {e} (재시도 {consecutive_fails}번째, {wait}초 후)")
                    time.sleep(wait)

        self.sse_thread = threading.Thread(target=listen, daemon=True)
        self.sse_thread.start()

    def _update_sse_port(self, new_port):
        """GUI 재시작 시 SSE 포트 업데이트"""
        self._sse_port = new_port
        print(f"[SSE-IPC] Port updated to {new_port}")
    
    def show_window(self):
        """GUI 창 열기"""
        # 이미 창이 열려있는지 확인
        if self.gui_process:
            try:
                # 프로세스가 아직 실행 중인지 확인
                poll_result = self.gui_process.poll()
                if poll_result is None:
                    print("[창 열기] 이미 창이 열려있습니다.")
                    return
                else:
                    # 프로세스가 종료된 경우 None으로 설정
                    print(f"[창 열기] 이전 프로세스가 종료되었습니다 (exit code: {poll_result})")
                    self.gui_process = None
            except Exception as e:
                print(f"[창 열기] 프로세스 상태 확인 오류: {e}")
                self.gui_process = None
        
        print("[창 열기] GUI 창 열기 시도...")
        
        try:
            # 환경 변수 설정
            env = os.environ.copy()
            env['BELL_GUI_MODE'] = '1'
            env['BELL_IPC_PORT'] = '0' # 필요시 자동 할당 유도
            
            if getattr(sys, 'frozen', False):
                # PyInstaller 빌드 환경: 자기 자신을 GUI 모드로 실행
                executable = sys.executable
                args = [executable]
                print(f"[창 열기] 빌드 환경 실행: {executable}")
            else:
                # 개발 환경: gui_process.py 직접 실행
                executable = sys.executable
                backend_dir = os.path.dirname(os.path.abspath(__file__))
                gui_script = os.path.join(backend_dir, 'gui', 'gui_process.py')
                args = [executable, gui_script]
                print(f"[창 열기] 개발 환경 실행: {gui_script}")

            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                text=True,
                bufsize=1
            )
            self.gui_process = process
            self._start_output_reader(process)
            print(f"[창 열기] GUI 프로세스 시작됨 (PID: {process.pid})")
            
        except Exception as e:
            print(f"[창 열기] GUI 실행 오류: {e}")
            import traceback
            traceback.print_exc()

    def _start_output_reader(self, process):
        """GUI 프로세스의 출력을 읽어 포트 번호 확인"""
        import threading
        def read_output():
            for line in iter(process.stdout.readline, ''):
                print(f"[GUI] {line.strip()}")
                if "BELL_PORT:" in line:
                    try:
                        port = int(line.split("BELL_PORT:")[1].strip())
                        # 항상 새 포트로 SSE 리스너 재시작 (GUI 재시작 대응)
                        self._start_sse_listener(port)
                    except Exception:
                        pass
            process.stdout.close()

        threading.Thread(target=read_output, daemon=True).start()
    
    def quit(self):
        """애플리케이션 종료"""
        print("\n종료 중...")
        
        # 사용자 상태를 오프라인으로 설정 (Firestore 포함)
        try:
            user_data = self.user_manager.get_user()
            if user_data and user_data.get('id'):
                user_id = user_data.get('id')
                # 로컬 파일에 오프라인 상태 저장
                self.user_manager.save_user_status('offline')
                print(f"[종료] 로컬 파일에 오프라인 상태 저장: {user_id}")
                
                # Supabase(PostgreSQL)에 오프라인 상태 업데이트
                try:
                    from db_manager import DBManager
                    db = DBManager()
                    db.update_user_status(user_id, 'offline')
                    print(f"[종료] Supabase에 오프라인 상태 업데이트 완료: {user_id}")
                except Exception as db_error:
                    print(f"[종료] Supabase 상태 업데이트 실패: {db_error}")
        except Exception as e:
            print(f"[종료] 상태 설정 실패: {e}")
            import traceback
            traceback.print_exc()
        
        # GUI 프로세스 종료
        if self.gui_process:
            try:
                print(f"[종료] GUI 프로세스 종료 중 (PID: {self.gui_process.pid})")
                self.gui_process.terminate()
                try:
                    self.gui_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    print("[종료] GUI 프로세스 강제 종료")
                    self.gui_process.kill()
                    self.gui_process.wait()
            except Exception as e:
                print(f"[종료] GUI 프로세스 종료 오류: {e}")
                try:
                    if self.gui_process.poll() is None:
                        self.gui_process.kill()
                except:
                    pass
        
        # 트레이 아이콘 종료
        if self.tray_manager.icon:
            try:
                self.tray_manager.icon.stop()
            except:
                pass
        
        print("종료 완료")
        
        # 강제 종료
        import os
        os._exit(0)
    
    def run(self):
        """애플리케이션 실행"""
        print("시스템 트레이 설정 중...")
        
        # 트레이 아이콘 설정 (initial_status 유지해서 setup에서 덮어쓰지 않도록)
        icon = self.tray_manager.setup(current_status=self.tray_manager._impl.current_status)
        if not icon:
            print("트레이 설정 실패")
            return
        
        # macOS에서 Dock 숨기기 (pystray가 NSApp을 초기화하기 전에 설정)
        if sys.platform == 'darwin':
            def hide_from_dock():
                """메인 프로세스를 Dock에서 숨기기"""
                try:
                    import ctypes
                    from ctypes import c_int, c_void_p
                    libproc = ctypes.CDLL('/usr/lib/libproc.dylib')
                    libproc.TransformProcessType.restype = c_int
                    libproc.TransformProcessType.argtypes = [c_void_p, c_int]
                    pid = os.getpid()
                    result = libproc.TransformProcessType(ctypes.c_void_p(pid), 1)
                    if result == 0:
                        print("[메인] Dock에서 메인 프로세스 숨기기 완료 (TransformProcessType)")
                except Exception:
                    try:
                        from AppKit import NSApp, NSApplicationActivationPolicyAccessory
                        NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
                        print("[메인] Dock에서 메인 프로세스 숨기기 완료 (AppKit)")
                    except Exception:
                        pass
            
            # icon.run() 전에 설정
            hide_from_dock()
            
            # icon.run() 후에도 다시 설정 (pystray가 NSApp을 초기화할 수 있음)
            import threading
            def hide_after_tray_start():
                import time
                time.sleep(0.5)  # pystray가 초기화될 때까지 대기
                hide_from_dock()
            threading.Thread(target=hide_after_tray_start, daemon=True).start()
        
        print("트레이 아이콘 실행 중...")
        print("(메뉴 바에 아이콘이 나타나야 합니다)")
        print("(아이콘을 클릭하면 GUI 창이 열립니다)")
        
        # 처음 시작할 때 GUI 창 자동으로 열기
        import threading
        import time
        
        def open_initial_window():
            # 트레이가 완전히 초기화될 때까지 약간 대기
            time.sleep(0.5)
            print("[초기 실행] GUI 창 자동으로 열기")
            self.show_window()
        
        # 별도 스레드에서 GUI 창 열기 (트레이가 블로킹되기 전에)
        threading.Thread(target=open_initial_window, daemon=True).start()
        
        # pystray.run()은 블로킹 호출
        try:
            icon.run()
        except KeyboardInterrupt:
            print("\n종료 신호 수신")
            self.quit()
        except Exception as e:
            print(f"실행 오류: {e}")
            import traceback
            traceback.print_exc()
            self.quit()


def main():
    """메인 함수"""
    # GUI 전용 모드 체크 (무한 루프 방지)
    if os.environ.get('BELL_GUI_MODE') == '1':
        # GUI 전용 모드: gui_process만 실행
        if getattr(sys, 'frozen', False):
            if sys._MEIPASS not in sys.path:
                sys.path.insert(0, sys._MEIPASS)
        from gui import gui_process
        gui_process.run_gui()
        return
    
    # 메인 프로세스는 시스템 트레이에만 표시하고 Dock에서는 숨김
    # macOS에서 메인 프로세스가 Dock에 나타나지 않도록 설정
    if sys.platform == 'darwin':
        try:
            import ctypes
            from ctypes import c_int, c_void_p
            # TransformProcessType을 사용하여 Dock에서 숨기기
            libproc = ctypes.CDLL('/usr/lib/libproc.dylib')
            libproc.TransformProcessType.restype = c_int
            libproc.TransformProcessType.argtypes = [c_void_p, c_int]
            pid = os.getpid()
            result = libproc.TransformProcessType(ctypes.c_void_p(pid), 1)
            if result == 0:
                print("[메인] Dock에서 메인 프로세스 숨기기 완료 (시스템 트레이만 사용)")
        except Exception as e:
            # AppKit을 대체 방법으로 시도
            try:
                from AppKit import NSApp, NSApplicationActivationPolicyAccessory
                NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
                print("[메인] Dock에서 메인 프로세스 숨기기 완료 (AppKit)")
            except Exception:
                pass
    
    platform_name = PlatformDetector.get_platform_name()
    is_macos = PlatformDetector.is_macos()
    is_windows = PlatformDetector.is_windows()
    
    # 하드웨어 UUID 가져오기
    machine_id = get_hardware_uuid()
    
    print("=" * 50)
    print("Bell 애플리케이션 시작")
    print(f"플랫폼: {platform_name.upper()}")
    if machine_id:
        print(f"하드웨어 ID: {machine_id}")
    else:
        print("하드웨어 ID: 가져올 수 없음")
    print("=" * 50)
    
    if is_macos:
        print("✅ macOS 환경에서 실행됩니다.")
    elif is_windows:
        print("✅ Windows 환경에서 실행됩니다.")
    else:
        print(f"⚠️ {platform_name} 환경 - 일부 기능이 제한될 수 있습니다.")
    
    try:
        print("\n애플리케이션 초기화 중...")
        app = BellApp(machine_id=machine_id)  # 이미 가져온 machine_id 전달
        print("초기화 완료")
        print("실행 시작...")
        app.run()
    except Exception as e:
        print(f"치명적 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
