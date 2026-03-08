# Bell Backend

Bell 애플리케이션의 Python 백엔드 코드입니다.

## 구조

```
backend/
├── __init__.py
├── main.py                 # 메인 애플리케이션 진입점
├── config.py              # 설정 관리
├── data_manager.py         # 데이터 관리
├── user_status.py          # 사용자 상태 관리
├── platform_detector.py   # 플랫폼 감지
├── web_server.py           # 빌드된 프론트엔드 서빙 서버
├── notification/           # 알림 모듈
│   ├── notification_base.py
│   ├── notification_macos.py
│   ├── notification_windows.py
│   └── notification_manager.py
├── tray/                   # 시스템 트레이 모듈
│   ├── tray_base.py
│   ├── tray_macos.py
│   ├── tray_windows.py
│   └── tray_manager.py
└── gui/                    # GUI 모듈
    ├── gui_process.py      # webview GUI 프로세스
    └── main_window.py
```

## 설치

### Conda 환경 설정

```bash
# conda 환경 생성 (처음 한 번만)
conda create -n bell python=3.10

# conda 환경 활성화
conda activate bell
```

### Python 패키지 설치

필요한 Python 패키지 설치:

```bash
pip install -r ../requirements.txt
```

또는 개별 설치:

```bash
pip install pystray Pillow pywebview PyYAML websockets
```

## 사용 방법

**중요**: 실행 전에 conda 환경을 활성화하세요:

```bash
conda activate bell
```

### 1. 프론트엔드 빌드

프론트엔드를 먼저 빌드해야 합니다:

```bash
# 프로젝트 루트에서
cd frontend
npm install
npm run build
```

또는 빌드 스크립트 사용:

```bash
./build.sh
```

빌드된 파일은 `backend/gui/web/` 디렉토리에 생성됩니다.

### 2. 백엔드 실행

```bash
# 프로젝트 루트에서
python run.py
```

또는:

```bash
cd backend
python main.py
```

또는:

```bash
# 프로젝트 루트에서
python -m backend.main
```

## 웹 서버

`web_server.py`는 빌드된 프론트엔드를 HTTP 서버로 서빙합니다.

- 기본 포트: 자동 할당 (사용 가능한 포트)
- 서빙 디렉토리: `backend/gui/web/`
- SPA 라우팅 지원: 모든 경로를 `index.html`로 폴백

## GUI 프로세스

`gui/gui_process.py`는 별도 프로세스에서 실행되며:

1. 웹 서버를 시작하여 빌드된 프론트엔드를 서빙
2. webview 창을 열어 웹앱을 표시
3. JavaScript API를 통해 Python 기능 제공

## API

JavaScript에서 호출 가능한 Python API:

- `getUsers()`: 사용자 목록 반환
- `setStatus(status)`: 상태 설정
- `sendNotification(target_user_id, notification_type, message)`: 알림 전송
- `getMessages()`: 쪽지 목록 가져오기
- `markMessageRead(message_id)`: 쪽지 읽음 처리
- `deleteMessage(message_id)`: 쪽지 삭제
- `closeWindow()`: 창 닫기

