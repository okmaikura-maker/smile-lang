# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\user\\Desktop\\smile-lang\\smile\\__main__.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\user\\Desktop\\smile-lang\\smile\\grammar.lark', 'smile'), ('C:\\Users\\user\\Desktop\\smile-lang\\smile\\logo.svg', 'smile')],
    hiddenimports=['smile.compiler', 'smile.errors', 'smile.stdlib', 'smile.pypi_fetch', 'smile.lowlevel', 'smile.debugger', 'smile.lsp', 'smile.web', 'smile.gpu', 'smile.ffi', 'smile.compute', 'lark'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['bitsandbytes', 'torch', 'tensorflow', 'transformers', 'numpy', 'pandas', 'scipy', 'matplotlib', 'PIL', 'cv2', 'sklearn'],
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
    name='smile',
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
)
