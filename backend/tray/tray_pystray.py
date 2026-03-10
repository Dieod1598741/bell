import os
import sys
import threading
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as item
from plyer import notification
from .tray_base import BaseTrayManager

def resource_path(relative_path):
    """PyInstaller 표준 및 개발 환경을 고려한 결정적 리소스 경로 확인"""
    if hasattr(sys, '_MEIPASS'):
        # 1. 빌드 환경: _MEIPASS 루트 또는 tray 내 폴더
        for sub in ['.', 'tray', 'backend/tray']:
            p = os.path.join(sys._MEIPASS, sub, relative_path)
            if os.path.exists(p): return p
    
    # 2. 개발 환경: 현재 파일 기준 상대 경로
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(curr_dir, relative_path)
    if os.path.exists(p): return p
    
    return relative_path

class PystrayTrayManager(BaseTrayManager):
    """pystray와 PIL을 사용한 단일화된 트레이 관리자"""
    
    def __init__(self, on_show_window=None, on_quit=None, on_show_status=None, machine_id=None):
        # BaseTrayManager.__init__를 명시적으로 호출 (린트 오류 방지)
        BaseTrayManager.__init__(self, on_show_window, on_quit, on_show_status)
        self.pystray_icon = None
        self.current_status = 'offline'
        self.unread_count = 0
        
        # 아이콘 검색 (우선순위에 따라)
        self.icon_path = None
        for icon_name in ['bell_icon.png', 'bell_sys.png', 'icon.png']:
            path = resource_path(icon_name)
            if os.path.exists(path):
                self.icon_path = path
                break
        
        print(f"[Pystray] 초기화 완료. 아이콘 경로: {self.icon_path}")
        
    def _create_image(self, status='offline', count=0):
        """상태와 숫자가 반영된 동적 아이콘 생성"""
        try:
            if os.path.exists(self.icon_path):
                img = Image.open(self.icon_path).convert('RGBA')
            else:
                # 아이콘 파일이 없을 경우 빈 이미지 생성
                img = Image.new('RGBA', (64, 64), color=(255, 255, 255, 0))
            
            # 크기 조정 (트레이용 64x64 또는 32x32)
            img = img.resize((64, 64), Image.Resampling.LANCZOS)
            draw = ImageDraw.Draw(img)
            
            # 1. 상태 표시 (우측 하단 작은 원)
            status_colors = {
                'online': (0, 255, 0),    # Green
                'away': (255, 255, 0),     # Yellow
                'busy': (255, 0, 0),       # Red
                'offline': (128, 128, 128) # Gray
            }
            color = status_colors.get(status, (128, 128, 128))
            draw.ellipse((45, 45, 60, 60), fill=color, outline=(255, 255, 255))
            
            # 2. 알림 숫자 표시 (좌측 상단 빨간 원)
            if count > 0:
                draw.ellipse((5, 5, 30, 30), fill=(255, 0, 0))
                # 폰트 설정 (시스템 폰트 시도)
                try:
                    # macOS/Windows 기본 폰트 경로들
                    font_paths = ["/System/Library/Fonts/Helvetica.ttc", "C:\\Windows\\Fonts\\arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
                    font = None
                    for f_path in font_paths:
                        if os.path.exists(f_path):
                            font = ImageFont.truetype(f_path, 18)
                            break
                    if not font:
                        font = ImageFont.load_default()
                except:
                    font = ImageFont.load_default()
                
                text = str(count) if count < 100 else "99+"
                # 텍스트 중앙 맞춤
                bbox = draw.textbbox((0, 0), text, font=font)
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                draw.text(((35-w)/2, (35-h)/2 - 2), text, font=font, fill=(255, 255, 255))
                
            return img
        except Exception as e:
            print(f"[Pystray] 아이콘 생성 실패: {e}")
            return Image.new('RGB', (64, 64), color=(255, 255, 255))

    def setup(self, current_status='offline'):
        """트레이 설정 및 초기화"""
        self.current_status = current_status if current_status else 'offline'
        
        # 메뉴 구성
        menu = (
            item('앱 열기', self.on_show_window, default=True),
            item('상태: ' + self.current_status, lambda: None, enabled=False),
            item.separator if hasattr(item, 'separator') else pystray.Menu.SEPARATOR,
            item('종료', self.on_quit)
        )
        
        # 아이콘 객체 생성
        self.pystray_icon = pystray.Icon(
            "Bell",
            self._create_image(self.current_status, self.unread_count),
            "Bell - 알람 시스템",
            menu
        )
        return self.pystray_icon

    def start(self):
        """트레이 실행 (별도 스레드)"""
        # setup()이 호출되지 않았으면 기본 설정으로 호출
        if self.pystray_icon is None:
            self.setup()
            
        if self.pystray_icon:
            self._running = True
            threading.Thread(target=self.pystray_icon.run, daemon=True).start()
            print("[Pystray] 트레이 시작됨")

    def stop(self):
        """트레이 중지"""
        if self.pystray_icon:
            self.pystray_icon.stop()
            self._running = False
            print("[Pystray] 트레이 중지됨")

    def update_icon(self, status: str = None, count: int = None):
        """아이콘 이미지 실시간 업데이트"""
        if status: self.current_status = status
        if count is not None: self.unread_count = count
        
        if self.pystray_icon:
            self.pystray_icon.icon = self._create_image(self.current_status, self.unread_count)
            # 메뉴 내 상태 표시 텍스트 갱신을 위해 메뉴 재생성 고려 (필요시)

    def show_notification(self, title, message):
        """시스템 알림 출력 (plyer 활용)"""
        try:
            notification.notify(
                title=title,
                message=message,
                app_name='Bell',
                app_icon=self.icon_path if os.path.exists(self.icon_path) else None,
                timeout=5
            )
        except Exception as e:
            print(f"[Pystray] 알림 출력 실패: {e}")
