# -*- mode: python ; coding: utf-8 -*-
# Optimized PyInstaller spec for AI Document Organizer
# - Excludes test modules to reduce size (~100MB savings)
# - Uses new google-genai SDK (replaces deprecated google-generativeai)

block_cipher = None

a = Analysis(
    ['../main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../assets/generated-icon.png', '.'),
        ('../docs', 'docs'),
    ],
    hiddenimports=[
        # Google Gemini AI (new SDK)
        'google.genai',
        'google.genai.types',
        'google.genai._api_client',
        'google.auth',
        'google.auth.transport.requests',
        # OpenAI
        'openai',
        'openai.types',
        'openai._client',
        # Data processing
        'pandas',
        'pandas.io.formats.style',
        'openpyxl',
        'openpyxl.styles',
        'numpy',
        # Document processing
        'docx',
        'docx.shared',
        'PyPDF2',
        'PyPDF2.generic',
        # Web/parsing
        'chardet',
        'bs4',
        # Other
        'PIL',
        'PIL.Image',
        'psutil',
        'pydantic',
        'pydantic.fields',
        'pydantic_core',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # ===== PANDAS TEST MODULES (~100MB savings) =====
        'pandas.tests',
        'pandas.tests.apply',
        'pandas.tests.arithmetic',
        'pandas.tests.arrays',
        'pandas.tests.base',
        'pandas.tests.computation',
        'pandas.tests.config',
        'pandas.tests.construction',
        'pandas.tests.copy_view',
        'pandas.tests.dtypes',
        'pandas.tests.extension',
        'pandas.tests.frame',
        'pandas.tests.generic',
        'pandas.tests.groupby',
        'pandas.tests.indexes',
        'pandas.tests.indexing',
        'pandas.tests.interchange',
        'pandas.tests.internals',
        'pandas.tests.io',
        'pandas.tests.libs',
        'pandas.tests.plotting',
        'pandas.tests.reductions',
        'pandas.tests.resample',
        'pandas.tests.reshape',
        'pandas.tests.scalar',
        'pandas.tests.series',
        'pandas.tests.strings',
        'pandas.tests.tools',
        'pandas.tests.tseries',
        'pandas.tests.tslibs',
        'pandas.tests.util',
        'pandas.tests.window',
        
        # ===== NUMPY TEST MODULES =====
        'numpy.tests',
        'numpy.testing',
        'numpy.distutils',
        'numpy.f2py',
        
        # ===== OTHER TEST/DEV MODULES =====
        'pytest',
        'pytest_asyncio',
        'hypothesis',
        'unittest',
        'test',
        'tests',
        
        # ===== UNUSED HEAVY MODULES =====
        'matplotlib',
        'matplotlib.pyplot',
        'scipy',
        'scipy.stats',
        'IPython',
        'jupyter',
        'notebook',
        'ipykernel',
        'nbformat',
        'nbconvert',
        'tkinter.test',
        # Note: Don't exclude distutils/setuptools - required by PyInstaller
        
        # ===== UNUSED DB MODULES =====
        'sqlite3.test',
    ],
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
    name='AI Document Organizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../assets/generated-icon.png',
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI Document Organizer',
)