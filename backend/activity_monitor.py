"""사용자 활동 모니터링 (마우스 움직임 감지)"""
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Callable
from platform_detector import PlatformDetector

try:
    from pynput import mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("[ActivityMonitor] pynput이 설치되지 않았습니다. 마우스 움직임 감지가 비활성화됩니다.")


class ActivityMonitor:
    """사용자 활동 모니터링 클래스"""
    
    def __init__(self, on_activity_change: Optional[Callable[[bool], None]] = None, on_backend_request: Optional[Callable[[], None]] = None):
        """
        Args:
            on_activity_change: 활동 상태 변경 시 호출할 콜백 함수 (is_active: bool)
            on_backend_request: 백엔드 요청이 있었는지 확인하는 콜백 함수 (요청이 있으면 True 반환)
        """
        self.on_activity_change = on_activity_change
        self.on_backend_request = on_backend_request
        self.last_activity_time = datetime.now()
        self.last_backend_request_time = datetime.now()
        self.is_active = True
        self.monitoring = False
        self.mouse_listener = None
        self.monitor_thread = None
        self.idle_threshold_minutes = 5  # 5분간 활동 없으면 자리비움
        
        if not PYNPUT_AVAILABLE:
            print("[ActivityMonitor] pynput이 없어 마우스 움직임 감지가 불가능합니다.")
    
    def _on_mouse_move(self, x, y):
        """마우스 움직임 감지"""
        was_active = self.is_active
        self.last_activity_time = datetime.now()
        self.is_active = True
        
        # 비활성에서 활성으로 변경된 경우
        if not was_active and self.on_activity_change:
            self.on_activity_change(True)
    
    def _check_idle(self):
        """주기적으로 활동 상태 확인"""
        while self.monitoring:
            try:
                now = datetime.now()
                
                # 마우스 이벤트를 제어할 수 없는 경우: 백엔드 요청 체크
                if not PYNPUT_AVAILABLE and self.on_backend_request:
                    # 백엔드 요청이 있었는지 확인
                    has_request = self.on_backend_request()
                    if has_request:
                        self.last_backend_request_time = now
                        elapsed_activity = (now - self.last_backend_request_time).total_seconds() / 60
                    else:
                        # 5분 이내 요청이 없으면 자리비움
                        elapsed_activity = self.idle_threshold_minutes + 1
                else:
                    # 마우스 이벤트로 활동 체크
                    elapsed_activity = (now - self.last_activity_time).total_seconds() / 60
                
                if elapsed_activity >= self.idle_threshold_minutes:
                    # 활동 없음 (자리비움)
                    if self.is_active:
                        self.is_active = False
                        if self.on_activity_change:
                            self.on_activity_change(False)
                else:
                    # 활동 있음 (온라인)
                    if not self.is_active:
                        self.is_active = True
                        if self.on_activity_change:
                            self.on_activity_change(True)
                
                # 1분마다 체크
                time.sleep(60)
            except Exception as e:
                print(f"[ActivityMonitor] 활동 체크 오류: {e}")
                time.sleep(60)
    
    def update_backend_request_time(self):
        """백엔드 요청이 있었을 때 호출 (마우스 이벤트를 제어 못할 때 사용)"""
        self.last_backend_request_time = datetime.now()
        if not self.is_active:
            self.is_active = True
            if self.on_activity_change:
                self.on_activity_change(True)
    
    def start(self):
        """활동 모니터링 시작"""
        if not PYNPUT_AVAILABLE:
            print("[ActivityMonitor] pynput이 없어 모니터링을 시작할 수 없습니다.")
            return False
        
        if self.monitoring:
            print("[ActivityMonitor] 이미 모니터링 중입니다.")
            return False
        
        try:
            # 마우스 리스너 시작
            self.mouse_listener = mouse.Listener(on_move=self._on_mouse_move)
            self.mouse_listener.start()
            
            # 활동 체크 스레드 시작
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._check_idle, daemon=True)
            self.monitor_thread.start()
            
            print("[ActivityMonitor] 활동 모니터링 시작됨")
            return True
        except Exception as e:
            print(f"[ActivityMonitor] 모니터링 시작 실패: {e}")
            return False
    
    def stop(self):
        """활동 모니터링 중지"""
        self.monitoring = False
        
        if self.mouse_listener:
            try:
                self.mouse_listener.stop()
            except:
                pass
            self.mouse_listener = None
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
            self.monitor_thread = None
        
        print("[ActivityMonitor] 활동 모니터링 중지됨")
    
    def get_is_active(self) -> bool:
        """현재 활동 상태 반환"""
        return self.is_active
    
    def get_last_activity_time(self) -> datetime:
        """마지막 활동 시간 반환"""
        return self.last_activity_time


if __name__ == '__main__':
    """테스트"""
    def on_change(is_active):
        status = "활동 중" if is_active else "자리비움"
        print(f"[테스트] 상태 변경: {status}")
    
    monitor = ActivityMonitor(on_activity_change=on_change)
    monitor.start()
    
    try:
        print("활동 모니터링 테스트 중... (Ctrl+C로 종료)")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop()
        print("테스트 종료")

