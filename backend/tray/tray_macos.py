"""macOS 시스템 트레이 관리자"""
import pystray
from PIL import Image, ImageDraw
import threading
from typing import Optional
import sys
import os

# backend 폴더를 경로에 추가
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from machine_id import get_hardware_uuid

class MacOSTrayManager:
    """macOS 전용 트레이 관리자"""
    
    def __init__(self, on_show_window=None, on_quit=None, on_show_status=None, machine_id=None):
        self.on_show_window = on_show_window
        self.on_quit = on_quit
        self.on_show_status = on_show_status
        self.icon = None
        self._running = False
        self.notification_count = 0
        # machine_id를 파라미터로 받거나, 없으면 가져오기
        self.machine_id = machine_id or get_hardware_uuid()
    
    def _create_icon_image(self) -> Image.Image:
        """트레이 아이콘 이미지 생성 (PNG 파일 사용)"""
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
                canvas_size = 24  # 캔버스 크기
                
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
                    badge_size = 10
                    badge_x0 = canvas_size - badge_size
                    badge_y0 = 0
                    badge_x1 = canvas_size
                    badge_y1 = badge_size
                    
                    # 빨간색 원형 배지
                    draw.ellipse([badge_x0, badge_y0, badge_x1, badge_y1], fill='#FF3B30', outline='white', width=1)
                    
                    # 숫자 텍스트 (간단하게 '.' 또는 '+' 정도로 표현하거나 숫자가 작으면 숫자 표시)
                    # 실제 폰트를 로드하기 어려우므로 작은 흰색 점이나 숫자를 픽셀로 그리기
                    if self.notification_count < 10:
                        text = str(self.notification_count)
                        # 대략적인 텍스트 위치 계산 (내장 폰트 사용 시도)
                        try:
                            from PIL import ImageFont
                            # macOS 기본 폰트 경로 시도
                            font_paths = [
                                "/System/Library/Fonts/Helvetica.ttc",
                                "/System/Library/Fonts/Cache/Arial.ttf",
                                "/Library/Fonts/Arial.ttf"
                            ]
                            font = None
                            for path in font_paths:
                                if os.path.exists(path):
                                    font = ImageFont.truetype(path, 8)
                                    break
                            
                            if font:
                                # draw.text((badge_x0 + 2, badge_y0 - 1), text, fill='white', font=font)
                                # getbbox is better
                                bbox = draw.textbbox((0, 0), text, font=font)
                                text_w = bbox[2] - bbox[0]
                                text_h = bbox[3] - bbox[1]
                                draw.text((badge_x0 + (badge_size-text_w)/2, badge_y0 + (badge_size-text_h)/2 - 1), text, fill='white', font=font)
                        except:
                            # 폰트 로드 실패 시 그냥 빨간 점만 유지 또는 작은 사각형으로 숫자 흉내
                            pass

                return canvas
            except Exception as e:
                print(f"[트레이] PNG 파일 로드 실패: {e}, 기본 아이콘 사용")
        
        # PNG 파일이 없거나 로드 실패 시 기본 아이콘 생성 (작은 원형)
        image = Image.new('RGBA', (32, 32), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        # 18x18 원을 32x32 캔버스 중앙에 배치
        draw.ellipse([7, 7, 25, 25], fill='#FFD700', outline='#FFA500', width=1)
        return image
    
    def _create_menu(self, current_status=None) -> pystray.Menu:
        """트레이 메뉴 생성 (상태 제거, 간단하게)"""
        menu_items = []
        
        # 창 열기
        if self.on_show_window:
            menu_items.append(
                pystray.MenuItem('창 열기', self._on_show_window)
            )
            menu_items.append(pystray.Menu.SEPARATOR)
        
        # 종료
        if self.on_quit:
            menu_items.append(
                pystray.MenuItem('종료', self._on_quit)
            )
        
        return pystray.Menu(*menu_items)
    
    def _on_show_window(self, icon, item):
        """창 열기 메뉴 클릭"""
        if self.on_show_window:
            self.on_show_window()
    
    def _on_quit(self, icon, item):
        """종료 메뉴 클릭"""
        import threading
        def do_quit():
            if self.on_quit:
                self.on_quit()
            if self.icon:
                self.icon.stop()
        
        thread = threading.Thread(target=do_quit, daemon=True)
        thread.start()
    
    def _on_click(self, icon):
        """트레이 아이콘 클릭 핸들러 (클릭 시 바로 창 열기)"""
        if self.on_show_window:
            self.on_show_window()
    
    def setup(self, current_status=None):
        """트레이 아이콘 설정 (상태 파라미터 무시)"""
        if self._running:
            return
        
        image = self._create_icon_image()
        menu = self._create_menu()  # 상태 제거
        
        # macOS에서 클릭 시 바로 창이 열리도록 default_action 사용
        # 메뉴는 오른쪽 클릭(또는 Ctrl+클릭)에서 열림
        machine_id_short = self.machine_id[:8] if self.machine_id else 'N/A'
        title = f"Bell (ID: {machine_id_short})"
        tooltip = f"Bell 알람 시스템 (ID: {machine_id_short})"
        self.icon = pystray.Icon(title, image, tooltip, menu, default_action=self._on_click)
        
        self._running = True
        return self.icon
    
    def start(self):
        """트레이 시작 (호환성)"""
        pass
    
    def stop(self):
        """트레이 종료"""
        self._running = False
        if self.icon:
            self.icon.stop()
    
    def update_icon(self, status: str = None, notification_count: int = None):
        """아이콘 업데이트 (알림 배지 포함)"""
        if notification_count is not None:
            self.notification_count = notification_count
        
        if self.icon:
            self.icon.icon = self._create_icon_image()
    
    def update_menu(self, current_status=None):
        """메뉴 업데이트 (사용 안 함)"""
        pass

