#!/bin/bash
# macOS 빌드 스크립트

set -e

echo "=========================================="
echo "Bell 애플리케이션 - macOS 빌드"
echo "=========================================="

# 1. 프론트엔드 빌드
echo ""
echo "1. 프론트엔드 빌드 중..."
cd frontend
npm install
npm run build
cd ..

# 2. 가상환경 및 PyInstaller 확인
echo ""
echo "2. 가상환경 및 PyInstaller 확인 중..."

if [ -d ".venv" ]; then
    echo "   가상환경(.venv) 발견. 활성화 중..."
    source .venv/bin/activate
fi

if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller가 설치되지 않았습니다. 설치 중..."
    pip install pyinstaller
fi

# 3. 프론트엔드 빌드 결과 확인
echo ""
echo "3. 프론트엔드 빌드 결과 확인 중..."
if [ ! -d "backend/gui/web" ]; then
    echo "❌ 오류: backend/gui/web 폴더를 찾을 수 없습니다."
    echo "   프론트엔드 빌드가 제대로 완료되었는지 확인하세요."
    exit 1
fi

# 3-1. 아이콘 파일 확인 및 변환
echo ""
echo "3-1. 아이콘 파일 확인 중..."
ICON_PNG=""
ICON_ICNS="backend/tray/icon.icns"

# bell_icon.png 파일 찾기
for dir in "." "backend" "backend/tray" "frontend" "frontend/public" "frontend/src/assets"; do
    if [ -f "$dir/bell_icon.png" ]; then
        ICON_PNG="$dir/bell_icon.png"
        break
    fi
done

if [ -n "$ICON_PNG" ]; then
    echo "   ✅ PNG 아이콘 파일 발견: $ICON_PNG"
    
    # .icns 파일이 없거나 유효하지 않으면 변환
    NEED_CONVERT=false
    if [ ! -f "$ICON_ICNS" ]; then
        NEED_CONVERT=true
        echo "   .icns 파일이 없습니다. 변환 중..."
    else
        FILE_TYPE=$(file -b "$ICON_ICNS" 2>/dev/null || echo "")
        if [[ "$FILE_TYPE" != *"Mac OS X icon"* ]] && [[ "$FILE_TYPE" != *"Apple icon"* ]]; then
            NEED_CONVERT=true
            echo "   기존 .icns 파일이 유효하지 않습니다. 다시 변환 중..."
        fi
    fi
    
    if [ "$NEED_CONVERT" = true ]; then
        # iconset 디렉토리 생성
        ICONSET_DIR="icon_temp.iconset"
        rm -rf "$ICONSET_DIR"
        mkdir -p "$ICONSET_DIR"
        
        # sips를 사용하여 다양한 크기 생성
        echo "   아이콘 크기 변환 중..."
        sips -z 16 16 "$ICON_PNG" --out "$ICONSET_DIR/icon_16x16.png" > /dev/null 2>&1
        sips -z 32 32 "$ICON_PNG" --out "$ICONSET_DIR/icon_16x16@2x.png" > /dev/null 2>&1
        sips -z 32 32 "$ICON_PNG" --out "$ICONSET_DIR/icon_32x32.png" > /dev/null 2>&1
        sips -z 64 64 "$ICON_PNG" --out "$ICONSET_DIR/icon_32x32@2x.png" > /dev/null 2>&1
        sips -z 128 128 "$ICON_PNG" --out "$ICONSET_DIR/icon_128x128.png" > /dev/null 2>&1
        sips -z 256 256 "$ICON_PNG" --out "$ICONSET_DIR/icon_128x128@2x.png" > /dev/null 2>&1
        sips -z 256 256 "$ICON_PNG" --out "$ICONSET_DIR/icon_256x256.png" > /dev/null 2>&1
        sips -z 512 512 "$ICON_PNG" --out "$ICONSET_DIR/icon_256x256@2x.png" > /dev/null 2>&1
        sips -z 512 512 "$ICON_PNG" --out "$ICONSET_DIR/icon_512x512.png" > /dev/null 2>&1
        sips -z 1024 1024 "$ICON_PNG" --out "$ICONSET_DIR/icon_512x512@2x.png" > /dev/null 2>&1
        
        # iconutil로 .icns 파일 생성
        iconutil -c icns "$ICONSET_DIR" -o "$ICON_ICNS" 2>/dev/null
        
        # 임시 디렉토리 정리
        rm -rf "$ICONSET_DIR"
        
        if [ -f "$ICON_ICNS" ]; then
            echo "   ✅ .icns 파일 생성 완료: $ICON_ICNS"
        else
            echo "   ⚠️  .icns 파일 생성 실패. 기본 아이콘을 사용합니다."
        fi
    else
        echo "   ✅ 기존 .icns 파일 사용: $ICON_ICNS"
    fi
else
    echo "   ⚠️  bell_icon.png 파일을 찾을 수 없습니다."
fi

# 4. 기존 빌드 파일 정리
echo ""
echo "4. 기존 빌드 파일 정리 중..."
# *.spec을 삭제할 때 수동으로 작성한 Bell.spec은 제외합니다.
rm -rf build dist
find . -name "*.spec" ! -name "Bell.spec" -delete

# 5. macOS 앱 빌드
echo ""
echo "5. Bell.spec을 사용하여 macOS 앱 빌드 중..."

# .env 파일 체크 (필요시 .env.example 복사)
if [ ! -f "backend/.env" ] && [ -f "backend/.env.example" ]; then
    echo "   ⚠️  backend/.env 파일이 없습니다. .env.example을 복사합니다."
    cp backend/.env.example backend/.env
fi

pyinstaller --clean \
    --noconfirm \
    Bell.spec

echo ""
echo "✅ macOS 빌드 완료!"
echo "   빌드 결과: dist/Bell.app"
echo ""
echo "설치 파일 생성 중..."
cd dist
if [ -d "Bell.app" ]; then
    hdiutil create -volname "Bell" -srcfolder "Bell.app" -ov -format UDZO "Bell.dmg"
    echo ""
    echo "✅ macOS 설치 파일 생성 완료!"
    echo "   설치 파일: dist/Bell.dmg"
else
    echo "❌ 오류: Bell.app을 찾을 수 없습니다."
    exit 1
fi
cd ..

echo ""
echo "✅ macOS 설치 파일 생성 완료!"
echo "   설치 파일: dist/Bell.dmg"

