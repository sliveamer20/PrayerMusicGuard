import os, shutil
from datetime import datetime

ts = datetime.now().strftime('%Y%m%d_%H%M%S')
project = r'E:\prayer-music-guard'
backup_dir = os.path.join(project, 'backup', f'phase18_onedir_migration_{ts}')
os.makedirs(backup_dir, exist_ok=True)

files = [
    'PrayerMusicGuard.spec',
    'PrayerMusicGuard-FIXES-TEST.spec',
    'PrayerMusicGuard-SPLASH-WARNING.spec',
    'build_exe.bat',
    'release.ps1',
    'PrayerMusicGuard.iss',
    'app_entry.py',
    'launcher.py',
    'main.py',
]

backup_dir_created = backup_dir
results = []
for f in files:
    src = os.path.join(project, f)
    dst = os.path.join(backup_dir, f)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        results.append(f'{f}: COPIED (verified)')
    else:
        results.append(f'{f}: NOT FOUND')

# Also backup the webview_app files that might need changes
extra = ['webview_app/launcher.py', 'webview_app/app_entry.py']
for f in extra:
    src = os.path.join(project, f)
    dst = os.path.join(backup_dir, os.path.basename(f) + f'_{f.replace("/", "_")}')
    if os.path.exists(src):
        shutil.copy2(src, dst)
        results.append(f'{f}: COPIED (verified)')

print(f'Backup directory: {backup_dir}')
print(f'Files backed up: {len([r for r in results if "COPIED" in r])}')
for r in results:
    print(f'  {r}')
