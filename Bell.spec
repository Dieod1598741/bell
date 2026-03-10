# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# 프로젝트 루트 및 backend 경로
project_root = os.path.abspath(os.getcwd())
backend_path = os.path.join(project_root, 'backend')

# 추가 데이터 파일들
added_files = [
    ('backend/gui/web', 'backend/gui/web'),
    ('backend/tray/icon.icns', 'backend/tray'),
    ('backend/tray/bell_icon.png', 'backend/tray'),
    ('backend/tray/bell_icon.png', '.'), # 루트에도 추가 (탐색 용이성)
    ('backend/.env', 'backend'), # 로컬 테스트용 .env 포함
]

# Hidden imports - 필요시 추가
hidden_imports = [
    'pystray',
    'PIL',
    'plyer',
    'psycopg2',
    'dotenv',
    'webview',
    'certifi',
]

a = Analysis(
    ['backend/main.py'],
    pathex=[project_root, backend_path],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == 'win32':
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='Bell',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='backend/tray/bell_icon.png',
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='Bell',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='backend/tray/icon.icns',
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='Bell',
    )

    app = BUNDLE(
        coll,
        name='Bell.app',
        icon='backend/tray/icon.icns',
        bundle_identifier='com.bell.app',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'False',
            'NSAppleEventsUsageDescription': 'Bell requires access to show notifications.',
        },
    )
