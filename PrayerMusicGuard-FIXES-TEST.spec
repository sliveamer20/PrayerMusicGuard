# -*- mode: python ; coding: utf-8 -*-
import os

from PyInstaller.utils.hooks import collect_all, collect_data_files

try:
    PROJECT_ROOT = os.path.abspath(SPECPATH)
except NameError:
    PROJECT_ROOT = os.path.abspath(os.getcwd())

WEBVIEW_APP = os.path.join(PROJECT_ROOT, "webview_app")

datas = [
    ("assets", "assets"),
    (os.path.join(PROJECT_ROOT, "main.py"), "."),
    (os.path.join(WEBVIEW_APP, "webview_main.py"), "webview_app"),
    (os.path.join(WEBVIEW_APP, "backend_api.py"), "webview_app"),
    (os.path.join(WEBVIEW_APP, "platform_check.py"), "webview_app"),
    (os.path.join(WEBVIEW_APP, "frontend"), os.path.join("webview_app", "frontend")),
]

binaries = []

hiddenimports = [
    "webview",
    "clr",
    "clr_loader",
    "pystray",
    "main",
    "launcher",
    "app_entry",
    "platform_check",
    "backend_api",
    "webview_main",
]

tmp_ret = collect_all("pystray")
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# CRITICAL: the pywebview hook only collects webview/lib (the .NET WebView2
# DLLs). It does NOT collect webview/js (api.js, finish.js, polyfill.js, ...)
# which pywebview loads at runtime to inject window.pywebview. Without them the
# bridge is never created inside the frozen EXE and every API call fails with
# "bridge unavailable". Bundle the js resources explicitly.
datas += collect_data_files('webview', subdir='js')


block_cipher = None


a = Analysis(
    [os.path.join(WEBVIEW_APP, "app_entry.py")],
    pathex=[PROJECT_ROOT, WEBVIEW_APP],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PrayerMusicGuard-v1.2.7-FIXES-TEST',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icons\\prayer_music_guard.ico'],
)