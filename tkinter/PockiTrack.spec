# -*- mode: python ; coding: utf-8 -*-
# PockiTrack.spec — PyInstaller build configuration
# Run: pyinstaller PockiTrack.spec

import os
import glob
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

def safe_glob(pattern, dest):
    """Only include datas entry if matching files actually exist."""
    return [(pattern, dest)] if glob.glob(pattern) else []

block_cipher = None

# ── Collect all hidden imports ────────────────────────────────────────────────
hidden_imports = [
    # Supabase & HTTP
    'supabase',
    'httpx',
    'httpcore',
    'gotrue',
    'postgrest',
    'realtime',
    'storage3',
    'websockets',
# Document generation
    'docx',
    'docx.oxml',
    'docx.oxml.ns',
    'docx.shared',
    'docx.enum',
    'docx.enum.text',
    'lxml',
    'lxml.etree',
    'lxml._elementpath',

    # Auth / Security
    'werkzeug',
    'werkzeug.security',

    # dotenv
    'dotenv',
    'python_dotenv',

    # Tkinter (usually built-in, but just in case)
    'tkinter',
    'tkinter.font',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',

    # Image handling
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL.ImageDraw',

    # Standard lib used in db.py
    'smtplib',
    'email',
    'email.mime',
    'email.mime.multipart',
    'email.mime.text',
    'urllib.request',
    'uuid',
    'io',
    'ctypes',

    # Screens
    'screens.sidebar',
    'screens.start_screen',
    'screens.login_screen',
    'screens.home_screen',
    'screens.history_screen',
    'screens.wallet_screen',
    'screens.profile_screen',
    'screens.forgotpass_screen',
    'screens.change_password_screen',

    # App modules
    'db',
    'constants',
    'email_templates',
    'widgets',
]

# ── Data files (assets) ───────────────────────────────────────────────────────
# safe_glob only includes entries where files actually exist — no more errors
# for missing .jpg/.ico etc.
datas = (
    safe_glob('assets/fonts/*.ttf',     'assets/fonts') +
    safe_glob('assets/images/*.png',    'assets/images') +
    safe_glob('assets/images/*.jpg',    'assets/images') +
    safe_glob('assets/images/*.jpeg',   'assets/images') +
    safe_glob('assets/images/*.ico',    'assets/images') +
    safe_glob('assets/template/*.docx', 'assets/template') +
    safe_glob('.env',                   '.')
)

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── EXE ───────────────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PockiTrack',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # No terminal window (windowed mode)
    icon='assets/images/pocki_logo.ico',
)

# ── COLLECT (one-folder build) ────────────────────────────────────────────────
# One-folder is more reliable than --onefile for apps with many assets
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PockiTrack',
)
