# Bell 애플리케이션 빌드 가이드

## 사전 준비

### 1. 의존성 설치

```bash
# Python 패키지
pip install -r requirements.txt

# 프론트엔드 의존성
cd frontend
npm install
cd ..
```

### 2. .env 파일 확인

`backend/.env.example` 파일을 참고하여 `backend/.env` 파일을 생성하고 Supabase 연결 정보를 기입하세요.

## macOS 빌드

### 방법 1: 빌드 스크립트 사용 (권장)

```bash
chmod +x build_macos.sh
./build_macos.sh
```

### 방법 2: 수동 빌드 (Bell.spec 사용)

```bash
# 1. 프론트엔드 빌드
cd frontend
npm run build
cd ..

# 2. PyInstaller로 빌드
pyinstaller --clean Bell.spec

# 3. DMG 파일 생성
cd dist
hdiutil create -volname "Bell" -srcfolder "Bell.app" -ov -format UDZO "Bell.dmg"
```

### macOS 보안 및 공증 (Notarization) 안내

애플의 보안 정책으로 인해, 유료 개발자 계정으로 서명 및 공증되지 않은 앱은 실행 시 "악성 소프트웨어가 있는지 확인할 수 없습니다"라는 경고가 표시될 수 있습니다.

**해결 방법 (사용자 가이드):**
1. 앱을 처음 실행할 때 경고창이 뜨면 [취소]를 누릅니다.
2. [시스템 설정] > [개인정보 보호 및 보안]으로 이동합니다.
3. 하단에 있는 "Bell이(가) 차단되었습니다" 옆의 **[확인 없이 열기]** 버튼을 클릭합니다.
4. 다시 나타나는 팝업에서 **[열기]**를 선택합니다.

### 빌드 결과

- `dist/Bell.app` - macOS 애플리케이션
- `dist/Bell.dmg` - 설치 파일

## Windows 빌드

### 방법 1: 빌드 스크립트 사용

```cmd
build_windows.bat
```

### 방법 2: 수동 빌드 (Bell.spec 사용)

```cmd
REM 1. 프론트엔드 빌드
cd frontend
npm run build
cd ..

REM 2. PyInstaller로 빌드
pyinstaller --clean Bell.spec
```

### 빌드 결과

- `dist/Bell/` - Windows 애플리케이션 폴더
- `dist/Bell/Bell.exe` - 실행 파일

### Windows 설치 파일 생성 (선택사항)

NSIS 또는 Inno Setup을 사용하여 설치 파일을 만들 수 있습니다.

## 문제 해결

### 1. 모듈을 찾을 수 없는 오류

`--hidden-import` 옵션에 누락된 모듈을 추가하세요.

### 2. 아이콘 파일이 없는 경우

- macOS: `backend/tray/icon.icns` 파일 필요
- Windows: `backend/tray/icon.ico` 파일 필요

아이콘 파일이 없으면 `--icon` 옵션을 제거하세요.

### 3. 프론트엔드 파일을 찾을 수 없는 경우

빌드 전에 반드시 `backend/gui/web` 폴더가 생성되어 있는지 확인하세요.
(프론트엔드 빌드 결과물은 `backend/gui/web`에 생성됩니다)

### 4. Firebase 설정 파일 오류

`backend/firebase-service-account.json` 파일이 빌드에 포함되었는지 확인하세요.

## 배포 전 체크리스트

- [ ] 프론트엔드 빌드 완료 (`frontend/dist` 폴더 확인)
- [ ] Firebase 설정 파일 포함 확인
- [ ] 아이콘 파일 확인 (선택사항)
- [ ] 빌드된 앱 테스트
- [ ] 시스템 트레이 아이콘 표시 확인
- [ ] 알림 기능 테스트
- [ ] 로그인/로그아웃 기능 테스트

