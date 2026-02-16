# PyInstaller spec - 법인 영업 솔루션 exe 빌드
# 사용법: 빌드.bat 실행 (또는 아래 주석 순서대로 수동 실행)

# 1) 먼저 Chromium을 프로젝트 폴더에 설치해 두어야 함:
#    set PLAYWRIGHT_BROWSERS_PATH=%~dp0playwright_browsers
#    playwright install chromium

# 2) pyinstaller app.spec

# -*- mode: python ; coding: utf-8 -*-
import sys

block_cipher = None

# playwright_browsers 폴더가 있어야 함 (빌드.bat이 먼저 만듦)
from pathlib import Path
from PyInstaller.building.datastruct import Tree

playwright_browsers = Path('playwright_browsers')
datas = []
if playwright_browsers.is_dir():
    datas.extend(Tree(str(playwright_browsers), prefix='playwright_browsers'))
datas.extend(Tree('config', prefix='config'))
datas.extend(Tree('src', prefix='src'))
if Path('data').is_dir():
    datas.extend(Tree('data', prefix='data'))

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'flask',
        'openpyxl',
        'openpyxl.cell._writer',
        'playwright',
        'playwright.sync_api',
        'playwright._impl._api_types',
        'src.naver',
        'src.naver.constants',
        'src.naver.scraper',
        'src.naver.search',
        'src.naver.login',
        'src.bizno_net',
        'config',
        'config.settings',
    ],
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

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='법인영업솔루션',
    debug=False,
    bootloader_ignore_signatures=False,
    strip=False,
    upx=False,
    console=True,  # 콘솔 창 보이기 (로그/오류 확인용)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='법인영업솔루션',
)
