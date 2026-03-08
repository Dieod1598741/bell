# Bell - 알람 시스템

데스크톱 알람 애플리케이션

## 프로젝트 구조

```
bell/
├── frontend/          # Vue.js 프론트엔드
├── backend/           # Python 백엔드
├── requirements.txt   # Python 패키지 목록
└── build.sh          # 프론트엔드 빌드 스크립트
```

## 시작하기

### 1. Conda 환경 설정

```bash
# conda 환경 생성 (처음 한 번만)
conda create -n bell python=3.10

# conda 환경 활성화
conda activate bell
```

### 2. Python 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 프론트엔드 빌드

```bash
cd frontend
npm install
npm run build
```

또는 빌드 스크립트 사용:

```bash
./build.sh
```

### 4. 백엔드 실행

```bash
# conda 환경 활성화 확인
conda activate bell

# 실행
python run.py
```

또는:

```bash
cd backend
python main.py
```

## 개발 모드

### 프론트엔드 개발 서버

```bash
cd frontend
npm run dev
```

개발 서버는 `http://localhost:3003`에서 실행됩니다.

### 백엔드 실행

```bash
conda activate bell
python run.py
```

## 기술 스택

- **프론트엔드**: Vue 3, Element Plus, Tailwind CSS
- **백엔드**: Python, pywebview, pystray
- **실시간 통신**: WebSocket
- **데이터베이스**: 파일 기반 (향후 Firebase로 전환 예정)

## 주요 기능

- 사용자 상태 관리 (온라인, 자리비움, 방해금지, 오프라인)
- 실시간 메시지 및 채팅
- 인박스 (쪽지, 회의 요청, 메일 확인 요청)
- 시스템 트레이 통합
- 데스크톱 알림

## 문제 해결

### 404 오류

프론트엔드를 먼저 빌드해야 합니다:

```bash
cd frontend
npm run build
```

### WebSocket 연결 실패

백엔드가 실행 중인지 확인하고, `websockets` 패키지가 설치되어 있는지 확인하세요:

```bash
pip install websockets
```
