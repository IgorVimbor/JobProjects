# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_150725.py'],
    pathex=['.'],  # добавляем текущую директорию в путь
    binaries=[],
    datas=[('E:\\MyRepositories\\JobProjects\\Справка_по_рекламациям\\spravka_venv\\Lib\\site-packages\\tkinterdnd2', 'tkinterdnd2')],
    hiddenimports=['tkinterdnd2'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_private_assemblies=False,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Обработка_актов_160725_2image',
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
    icon=['IconGreen.ico'],
)
