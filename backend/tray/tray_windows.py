"""Windows 시스템 트레이 관리자"""
from typing import Optional
from .tray_base import BaseTrayManager
import sys
import os

# backend 폴더를 경로에 추가
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from machine_id import get_hardware_uuid

class WindowsTrayManager(BaseTrayManager):
    """Windows 전용 트레이 관리자"""
    
    def __init__(self, on_show_window=None, on_quit=None, on_show_status=None, machine_id=None):
        super().__init__(on_show_window, on_quit, on_show_status)
        self.notification_count = 0
        # machine_id를 파라미터로 받거나, 없으면 가져오기
        self.machine_id = machine_id or get_hardware_uuid()
    
    def setup(self, current_status=None):
        """트레이 아이콘 설정 (Windows)"""
        try:
            import pystray
            from PIL import Image, ImageDraw
            
            # tray 폴더 안의 bell_sys.png 파일 사용
            # PyInstaller로 빌드된 경우와 일반 실행 모두 지원
            if getattr(sys, 'frozen', False):
                # PyInstaller로 빌드된 경우: sys._MEIPASS에서 찾기
                base_path = sys._MEIPASS
                icon_path = os.path.join(base_path, 'backend', 'tray', 'bell_sys.png')
            else:
                # 일반 실행: 상대 경로 사용
                tray_dir = os.path.dirname(os.path.abspath(__file__))
                icon_path = os.path.join(tray_dir, 'bell_sys.png')
            
            if os.path.exists(icon_path):
                try:
                    image = Image.open(icon_path)
                    # RGBA 모드로 변환 (투명도 지원)
                    if image.mode != 'RGBA':
                        image = image.convert('RGBA')
                    
                    # 아이콘을 더 작게 리사이즈 (18x18)하고 32x32 캔버스에 중앙 배치하여 여백 추가
                    icon_size = 18  # 실제 아이콘 크기
                    canvas_size = 32  # 캔버스 크기
                    
                    # 원본 비율 유지하면서 리사이즈
                    width, height = image.size
                    aspect_ratio = width / height
                    
                    if aspect_ratio > 1:  # 가로가 더 긴 경우
                        new_width = icon_size
                        new_height = int(icon_size / aspect_ratio)
                    else:  # 세로가 더 긴 경우
                        new_height = icon_size
                        new_width = int(icon_size * aspect_ratio)
                    
                    # 아이콘 리사이즈
                    resized_icon = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # 32x32 투명 캔버스 생성
                    canvas = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
                    
                    # 중앙 배치
                    offset_x = (canvas_size - new_width) // 2
                    offset_y = (canvas_size - new_height) // 2
                    canvas.paste(resized_icon, (offset_x, offset_y), resized_icon)
                    
                    # 알림 배지 추가
                    if self.notification_count > 0:
                        draw = ImageDraw.Draw(canvas)
                        badge_size = 12
                        badge_x0 = canvas_size - badge_size
                        badge_y0 = 0
                        badge_x1 = canvas_size
                        badge_y1 = badge_size
                        
                        # 빨간색 원형 배지
                        draw.ellipse([badge_x0, badge_y0, badge_x1, badge_y1], fill='#FF3B30', outline='white', width=1)
                        
                        if self.notification_count < 10:
                            text = str(self.notification_count)
                            try:
                                from PIL import ImageFont
                                # Windows 기본 폰트 경로 시도
                                font_paths = [
                                    "C:/Windows/Fonts/arial.ttf",
                                    "C:/Windows/Fonts/tahoma.ttf"
                                ]
                                font = None
                                for path in font_paths:
                                    if os.path.exists(path):
                                        font = ImageFont.truetype(path, 9)
                                        break
                                
                                if font:
                                    bbox = draw.textbbox((0, 0), text, font=font)
                                    text_w = bbox[2] - bbox[0]
                                    text_h = bbox[3] - bbox[1]
                                    draw.text((badge_x0 + (badge_size-text_w)/2, badge_y0 + (badge_size-text_h)/2 - 1), text, fill='white', font=font)
                            except:
                                pass

                    image = canvas
                except Exception as e:
                    print(f"[트레이] PNG 파일 로드 실패: {e}, 기본 아이콘 사용")
                    # PNG 파일이 없거나 로드 실패 시 기본 아이콘 생성
                    image = Image.new('RGBA', (32, 32), color=(0, 0, 0, 0))
                    draw = ImageDraw.Draw(image)
                    draw.ellipse([7, 7, 25, 25], fill='#FFD700', outline='#FFA500', width=1)
            else:
                # PNG 파일이 없으면 기본 아이콘 생성
                image = Image.new('RGBA', (32, 32), color=(0, 0, 0, 0))
                draw = ImageDraw.Draw(image)
                draw.ellipse([7, 7, 25, 25], fill='#FFD700', outline='#FFA500', width=1)
            
            menu_items = []
            if self.on_show_window:
                menu_items.append(pystray.MenuItem('창 열기', self._on_show_window))
            menu_items.append(pystray.Menu.SEPARATOR)
            if self.on_quit:
                menu_items.append(pystray.MenuItem('종료', self._on_quit))
            
            menu = pystray.Menu(*menu_items)
            machine_id_short = self.machine_id[:8] if self.machine_id else 'N/A'
            title = f"Bell (ID: {machine_id_short})"
            tooltip = f"Bell 알람 시스템 (ID: {machine_id_short})"
            self.icon = pystray.Icon(title, image, tooltip, menu)
            self._running = True
            return self.icon
        except Exception as e:
            print(f"Windows 트레이 설정 실패: {e}")
            return None
    
    def _on_show_window(self, icon, item):
        """창 열기"""
        if self.on_show_window:
            self.on_show_window()
    
    def _on_quit(self, icon, item):
        """종료"""
        if self.on_quit:
            self.on_quit()
        if self.icon:
            self.icon.stop()
            
    def update_icon(self, status: str = None, notification_count: int = None):
        """아이콘 업데이트 (알림 배지 포함)"""
        if notification_count is not None:
            self.notification_count = notification_count
            
        # setup을 다시 호출하는 대신 이미지를 직접 교체하는 로직은 
        # pystray 버전에 따라 다를 수 있으나 pystray.Icon.icon 속성 변경 지원
        if self.icon:
            # 여기서는 setup의 로직을 일부분 중복해서 사용하거나 
            # 이미지 생성 로직을 별도 메서드로 분리해야 함
            # 편의상 setup의 이미지 로직을 재사용 (실제 구현 시 리팩토링 필요)
            self._update_icon_internal()

    def _update_icon_internal(self):
        """내부 이미지 업데이트 로직"""
        from PIL import Image, ImageDraw
        # (이미지 생성 로직 중복 - 리팩토링이 정석이나 여기서는 직접 구현)
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            icon_path = os.path.join(base_path, 'backend', 'tray', 'bell_sys.png')
        else:
            tray_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(tray_dir, 'bell_sys.png')
        
        if os.path.exists(icon_path):
            image = Image.open(icon_path).convert('RGBA')
            icon_size = 18
            canvas_size = 32
            width, height = image.size
            aspect_ratio = width / height
            if aspect_ratio > 1:
                new_width = icon_size
                new_height = int(icon_size / aspect_ratio)
            else:
                new_height = icon_size
                new_width = int(icon_size * aspect_ratio)
            resized_icon = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            canvas = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
            offset_x = (canvas_size - new_width) // 2
            offset_y = (canvas_size - new_height) // 2
            canvas.paste(resized_icon, (offset_x, offset_y), resized_icon)
            
            if self.notification_count > 0:
                draw = ImageDraw.Draw(canvas)
                badge_size = 12
                badge_x0 = canvas_size - badge_size
                badge_y0 = 0
                draw.ellipse([badge_x0, badge_y0, canvas_size, badge_size], fill='#FF3B30', outline='white', width=1)
                
            self.icon.icon = canvas










