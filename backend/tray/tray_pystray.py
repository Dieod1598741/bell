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
        """상태와 숫자가 반영된 동적 아이콘 생성 (macOS/Windows 크로스플랫폼)"""
        import platform
        is_windows = platform.system() == 'Windows'
        
        # 플랫폼별 아이콘 크기
        # macOS: 44px (레티나 @2x 대응 - pystray가 22px로 축소해서 메뉴바에 표시)
        # Windows: 32px (알림 영역 표준)
        SIZE = 32 if is_windows else 44

        try:
            # ─────────────────────────────────────────────────
            # 1. 캔버스 생성 (불투명 배경)
            # ─────────────────────────────────────────────────
            # Windows: 흰색 불투명(RGB) 캔버스
            # macOS:   투명(RGBA) 캔버스 위에 알파 합성 → OS가 메뉴바 배경 처리
            canvas = Image.new('RGBA', (SIZE, SIZE), (255, 255, 255, 255) if is_windows else (0, 0, 0, 0))

            # ─────────────────────────────────────────────────
            # 2. 아이콘 PNG 로드 및 합성
            # ─────────────────────────────────────────────────
            if self.icon_path and os.path.exists(self.icon_path):
                icon_img = Image.open(self.icon_path).convert('RGBA')
                icon_img = icon_img.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
                # paste의 세 번째 인자(mask=icon_img)가 핵심:
                # PNG의 알파 채널을 마스크로 활용 → 투명부분은 캔버스(배경)가 그대로, 불투명부분만 아이콘으로 채워짐
                canvas.paste(icon_img, (0, 0), icon_img)
            else:
                # 아이콘 파일 없으면 파란 둥근 사각형으로 대체
                draw_tmp = ImageDraw.Draw(canvas)
                m = SIZE // 6
                draw_tmp.rounded_rectangle([m, m, SIZE - m, SIZE - m], radius=SIZE // 5, fill=(59, 130, 246, 255))
                print(f"[Pystray] ⚠️ 아이콘 파일 없음, 기본 도형으로 대체. path={self.icon_path}")

            draw = ImageDraw.Draw(canvas)

            # ─────────────────────────────────────────────────
            # 3. 상태 표시 원 (우측 하단)
            # ─────────────────────────────────────────────────
            status_colors = {
                'online':  (52, 199,  89, 255),   # 초록
                'away':    (255, 204,   0, 255),   # 노랑
                'busy':    (255,  59,  48, 255),   # 빨강
                'offline': (142, 142, 147, 255),   # 회색
            }
            dot_color = status_colors.get(status, (142, 142, 147, 255))
            dot_r = max(6, SIZE // 5)              # 원 반지름
            pad = 1                                # 가장자리 여백
            dot_x0 = SIZE - dot_r - pad
            dot_y0 = SIZE - dot_r - pad

            # 흰색 테두리로 아이콘과 분리
            draw.ellipse(
                (dot_x0 - 1, dot_y0 - 1, dot_x0 + dot_r + 1, dot_y0 + dot_r + 1),
                fill=(255, 255, 255, 255)
            )
            draw.ellipse(
                (dot_x0, dot_y0, dot_x0 + dot_r, dot_y0 + dot_r),
                fill=dot_color
            )

            # ─────────────────────────────────────────────────
            # 4. 배지 (좌측 상단, 알림 개수)
            # ─────────────────────────────────────────────────
            if count > 0:
                badge_r = max(9, SIZE // 3)
                draw.ellipse((0, 0, badge_r, badge_r), fill=(255, 59, 48, 255))
                try:
                    font_paths = [
                        "/System/Library/Fonts/Helvetica.ttc",
                        "C:\\Windows\\Fonts\\arial.ttf",
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    ]
                    font = None
                    for fp in font_paths:
                        if os.path.exists(fp):
                            font = ImageFont.truetype(fp, max(7, badge_r - 4))
                            break
                    if not font:
                        font = ImageFont.load_default()
                except Exception:
                    font = ImageFont.load_default()

                text = str(count) if count < 10 else "9+"
                bbox = draw.textbbox((0, 0), text, font=font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                draw.text(
                    ((badge_r - tw) / 2, (badge_r - th) / 2 - 1),
                    text, font=font, fill=(255, 255, 255, 255)
                )

            # ─────────────────────────────────────────────────
            # 5. Windows 최종 처리: RGBA → RGB (pystray 호환)
            # ─────────────────────────────────────────────────
            if is_windows:
                bg = Image.new('RGB', (SIZE, SIZE), (255, 255, 255))
                bg.paste(canvas, mask=canvas.split()[3])
                return bg

            return canvas

        except Exception as e:
            print(f"[Pystray] 아이콘 생성 실패: {e}")
            import traceback; traceback.print_exc()
            return Image.new('RGB', (32, 32), color=(59, 130, 246))


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
