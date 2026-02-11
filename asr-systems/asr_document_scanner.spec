# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

project_root = Path(SPECPATH)
document_scanner_path = project_root / "document-scanner"
shared_path = project_root / "shared"

# Collect encodings module completely to fix ModuleNotFoundError
encodings_datas, encodings_binaries, encodings_hiddenimports = collect_all('encodings')

# Collect pydantic completely to fix validation errors
pydantic_datas, pydantic_binaries, pydantic_hiddenimports = collect_all('pydantic')
pydantic_core_datas, pydantic_core_binaries, pydantic_core_hiddenimports = collect_all('pydantic_core')

a = Analysis(
    [str(document_scanner_path / "main_scanner.py")],
    pathex=[
        str(document_scanner_path),
        str(shared_path),
        str(document_scanner_path / "services"),
        str(document_scanner_path / "gui"),
        str(document_scanner_path / "config"),
        str(shared_path / "core"),
        str(shared_path / "api"),
        str(shared_path / "utils")
    ],
    binaries=encodings_binaries + pydantic_binaries + pydantic_core_binaries,
    datas=[
        (str(document_scanner_path / "config" / "scanner_settings.py"), "config"),
        (str(document_scanner_path / "gui" / "assets"), "gui/assets"),
        (str(shared_path / "data"), "shared/data"),
    ] + encodings_datas + pydantic_datas + pydantic_core_datas,
    hiddenimports=[
        # Tkinter GUI
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',

        # HTTP client
        'aiohttp',
        'aiohttp.client',
        'aiohttp.connector',
        'requests',
        'urllib3',

        # Async support
        'asyncio',
        'asyncio.tasks',
        'asyncio.events',
        'asyncio.queues',
        'concurrent.futures',

        # Database (SQLite for offline queue)
        'sqlite3',
        'aiosqlite',

        # JSON and data processing
        'json',
        'orjson',
        'ujson',

        # File processing
        'pathlib',
        'mimetypes',
        'tempfile',

        # Image processing for scanner
        'PIL',
        'Pillow',
        'PIL.Image',
        'PIL.ImageTk',

        # Scanner hardware support
        'twain',  # If available
        'winscan',  # Windows scanning

        # Configuration
        'configparser',
        'yaml',
        'pydantic',

        # Crypto for secure communication
        'cryptography',

        # Logging
        'logging',
        'logging.handlers',

        # Shared modules
        'shared',
        'shared.core',
        'shared.core.models',
        'shared.core.exceptions',
        'shared.api',
        'shared.utils',

        # Document scanner modules
        'document_scanner',
        'document_scanner.services',
        'document_scanner.gui',
        'document_scanner.config',

        # Additional modules for proper packaging
        'email.mime.text',
        'email.mime.multipart',
        'http.cookies',
        'http.client',
        'mimetypes',
        'concurrent.futures',
    ] + encodings_hiddenimports + pydantic_hiddenimports + pydantic_core_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
        'fastapi',
        'uvicorn',
        'django',
        'flask',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ASR_Document_Scanner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI application, no console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(document_scanner_path / "gui" / "assets" / "scanner_icon.ico") if (document_scanner_path / "gui" / "assets" / "scanner_icon.ico").exists() else None,
    version_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ASR_Document_Scanner'
)