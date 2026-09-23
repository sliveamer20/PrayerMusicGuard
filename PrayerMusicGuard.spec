# -*- mode: python ; coding: utf-8 -*-
import os

from PyInstaller.utils.hooks import collect_all, collect_data_files
from PyInstaller.building.build_main import COLLECT
# Phase 20.46.B: PYZ (embedded bytecode) block-cipher encryption.
from PyInstaller.archive import pyz_crypto

try:
    PROJECT_ROOT = os.path.abspath(SPECPATH)
except NameError:
    PROJECT_ROOT = os.path.abspath(os.getcwd())

WEBVIEW_APP = os.path.join(PROJECT_ROOT, "webview_app")

# Phase 20.46.A: NO application .py file is shipped as readable data. The six
# application modules (main, uiverse_combobox, webview_app.backend_api,
# webview_app.launcher, webview_app.platform_check, webview_app.webview_main)
# are compiled into the PYZ archive through hiddenimports below and imported
# from there at runtime, so they must NOT appear in datas/COLLECT.
datas = [
    ("assets", "assets"),
    (os.path.join(WEBVIEW_APP, "splash.html"), "webview_app"),
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
    "uiverse_combobox",
    # Phase 20.57: auto-update core (webview_app/updater.py) and the semver
    # library it needs. packaging is already pinned (requirements-win7.txt);
    # both must be compiled into the PYZ so the frozen EXE can check for updates.
    "updater",
    "packaging",
    "packaging.version",
    # Phase 20.58: shared update UI state machine (webview_app/update_flow.py)
    # used by both the WebView2 bridge and the Tkinter fallback.
    "update_flow",
]

tmp_ret = collect_all("pystray")
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# CRITICAL: the pywebview hook only collects webview/lib (the .NET WebView2
# DLLs). It does NOT collect webview/js (api.js, finish.js, polyfill.js, ...)
# which pywebview loads at runtime to inject window.pywebview. Without them the
# bridge is never created inside the frozen EXE and every API call fails with
# "bridge unavailable". Bundle the js resources explicitly.
datas += collect_data_files('webview', subdir='js')


# Phase 20.46.B: encrypt the PYZ archive (the embedded application bytecode)
# with PyInstaller 5.13.2's block cipher, PyInstaller.archive.pyz_crypto
# .PyiBlockCipher. Analysis(cipher=...) embeds the derived runtime decryption
# key and adds the 'tinyaes' hidden import automatically; PYZ(cipher=...)
# encrypts the archive. The key itself lives ONLY in the local, git-ignored
# build-secret file below: it is read here at build time, is never placed in
# datas/hiddenimports (so it is never bundled), never appears in application
# source or the UI, and is required for a reproducible encrypted build.
_PYZ_KEY_FILE = os.path.join(PROJECT_ROOT, "pyz_crypto_key.txt")
if not os.path.isfile(_PYZ_KEY_FILE):
    raise SystemExit(
        "Phase 20.46.B: PYZ encryption key file not found: %s\n"
        "Create it with a random secret before building, e.g. with\n"
        "secrets.token_urlsafe(32) written to that path." % _PYZ_KEY_FILE)
with open(_PYZ_KEY_FILE, "r", encoding="utf-8") as _pyz_key_file:
    _PYZ_KEY = _pyz_key_file.read().strip()
if not _PYZ_KEY:
    raise SystemExit("Phase 20.46.B: PYZ encryption key file is empty: %s" % _PYZ_KEY_FILE)

block_cipher = pyz_crypto.PyiBlockCipher(key=_PYZ_KEY)


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
    [],
    exclude_binaries=True,
    name='PrayerMusicGuard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icons\\prayer_music_guard.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PrayerMusicGuard',
)
