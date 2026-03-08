@echo off
REM Windows 빌드 스크립트

echo ==========================================
echo Bell 애플리케이션 - Windows 빌드
echo ==========================================

REM 1. 프론트엔드 빌드
echo.
echo 1. 프론트엔드 빌드 중...
cd frontend
call npm install
call npm run build
cd ..

REM 2. PyInstaller 설치 확인
echo.
echo 2. PyInstaller 확인 중...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller가 설치되지 않았습니다. 설치 중...
    pip install pyinstaller
)

REM 3. 프론트엔드 빌드 결과 확인
echo.
echo 3. 프론트엔드 빌드 결과 확인 중...
if not exist "backend\gui\web" (
    echo ❌ 오류: backend\gui\web 폴더를 찾을 수 없습니다.
    echo    프론트엔드 빌드가 제대로 완료되었는지 확인하세요.
    exit /b 1
)

REM 4. Windows 앱 빌드
echo.
echo 4. Bell.spec을 사용하여 Windows 앱 빌드 중...

REM .env 파일 체크 (필요시 .env.example 복사)
if not exist "backend\.env" (
    if exist "backend\.env.example" (
        echo    ⚠️  backend\.env 파일이 없습니다. .env.example을 복사합니다.
        copy backend\.env.example backend\.env
    )
)

pyinstaller --clean ^
    --noconfirm ^
    Bell.spec

echo.
echo ✅ Windows 빌드 완료!
echo    빌드 결과: dist\Bell\
echo.
echo 설치 파일 생성을 위해 NSIS 또는 Inno Setup이 필요합니다.

