"""시스템 트레이 관리자 (플랫폼별 구현 선택)"""
import sys
import os
from typing import Optional
# backend 폴더를 경로에 추가
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
from platform_detector import PlatformDetector

def create_tray_manager(on_show_window=None, on_quit=None, on_show_status=None, machine_id=None, app_version='v0.0.0'):
    """pystray 기반 트레이 관리자 생성 (단일화)"""
    try:
        from .tray_pystray import PystrayTrayManager
        return PystrayTrayManager(on_show_window, on_quit, on_show_status, machine_id, app_version)
    except Exception as e:
        print(f"[TrayManager] Pystray 초기화 실패, 기본값으로 폴백: {e}")
        from .tray_base import BaseTrayManager
        return BaseTrayManager(on_show_window, on_quit, on_show_status)

# 호환성을 위한 클래스
class TrayManager:
    """시스템 트레이 관리자 (팩토리)"""
    
    def __init__(self, on_show_window=None, on_quit=None, on_show_status=None, machine_id=None, app_version='v0.0.0'):
        self._impl = create_tray_manager(on_show_window, on_quit, on_show_status, machine_id, app_version)
    
    def setup(self, current_status='offline'):
        """트레이 아이콘 설정"""
        return self._impl.setup(current_status)
    
    def start(self):
        """트레이 시작"""
        return self._impl.start()
    
    def stop(self):
        """트레이 종료"""
        return self._impl.stop()
    
    def update_icon(self, status: Optional[str] = None):
        """아이콘 업데이트"""
        return self._impl.update_icon(status)
    
    def update_menu(self, current_status=None):
        """메뉴 업데이트"""
        return self._impl.update_menu(current_status)
    
    @property
    def icon(self):
        """아이콘 객체"""
        return self._impl.icon
    
    @property
    def _running(self):
        """실행 상태"""
        return self._impl._running

