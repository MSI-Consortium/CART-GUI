# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['srt_analysis_deluxe_GUI.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pandas',
        'numpy',
        'scipy',
        'matplotlib',
        'sklearn',
        'PyQt5',
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'pingouin'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'notebook',
        'jupyter_client',
        'ipython',
        'ipykernel',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
    compress=True
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CART GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['AppIcon.ico'],
    optimize=2
)
