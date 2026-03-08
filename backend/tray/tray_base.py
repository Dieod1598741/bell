"""기본 트레이 관리자"""
from typing import Optional

class BaseTrayManager:
    """기본 트레이 관리자 (미지원 플랫폼용)"""
    
    def __init__(self, on_show_window=None, on_quit=None, on_show_status=None):
        self.on_show_window = on_show_window
        self.on_quit = on_quit
        self.on_show_status = on_show_status
        self.icon = None
        self._running = False
    
    def setup(self, current_status=None):
        """트레이 아이콘 설정"""
        print("⚠️ 이 플랫폼에서는 시스템 트레이를 지원하지 않습니다.")
        return None
    
    def start(self):
        """트레이 시작"""
        pass
    
    def stop(self):
        """트레이 종료"""
        self._running = False
    
    def update_icon(self, status: str = None):
        """아이콘 업데이트"""
        pass
    
    def update_menu(self, current_status=None):
        """메뉴 업데이트"""
        pass










