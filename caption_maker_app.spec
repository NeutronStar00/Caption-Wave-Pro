# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import whisper
from PyInstaller.utils.hooks import collect_all, collect_data_files

# Get the path to the Python standard library
stdlib_path = os.path.dirname(os.__file__)

# Add the standard library path to sys.path
sys.path.insert(0, stdlib_path)

# Increase recursion limit
sys.setrecursionlimit(5000)

# Collect whisper model files
whisper_model_dir = os.path.join(os.path.dirname(whisper.__file__), 'assets')
whisper_model_files = [(os.path.join(whisper_model_dir, f), 'whisper/assets') for f in os.listdir(whisper_model_dir)]

# Collect torch files
datas = []
binaries = []
hiddenimports = []

tmp_ret = collect_all('torch')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Add whisper data files
datas += collect_data_files('whisper')

# Add your application's resource files
added_files = [
    ('Gilroy-Bold.ttf', '.'),
    ('Gilroy-Heavy.ttf', '.'),
]

a = Analysis(
    ['caption_maker_app.py'],
    pathex=[stdlib_path],
    binaries=binaries,
    datas=whisper_model_files + added_files + datas,
    hiddenimports=['openai-whisper', 'moviepy', 'numpy', 'torch', 'tqdm', 'pathlib', 'PIL', 
                   'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtWidgets', 'PyQt6.QtGui'] + hiddenimports,
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='caption_maker_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Changed back to False to remove console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,  
)