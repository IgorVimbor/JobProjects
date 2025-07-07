# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Добавляем все подмодули в hidden imports
hidden_imports = [
    'analytics',
    'backup',
    'copier',
    'db_search',
    'engine_search',
    'enquiry_period',
    # добавьте все подмодули, которые используются в проекте
]

# Собираем все файлы данных
added_files = [
    ('analytics', 'analytics'),
    ('backup', 'backup'),
    ('copier', 'copier'),
    ('db_search', 'db_search'),
    ('engine_search', 'engine_search'),
    ('enquiry_period', 'enquiry_period'),
    # Добавьте все необходимые файлы данных
]

a = Analysis(
    ['app_main_wk-020725.py'],
    pathex=['.'],  # добавляем текущую директорию в путь
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='app_main_wk-020725',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # измените на True, если нужна консоль при запуске приложения
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['IconBZA.ico'],
)