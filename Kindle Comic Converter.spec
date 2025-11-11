# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['kcc.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['_cffi_backend'],
    hookspath=[],
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
    [],
    exclude_binaries=True,
    name='Kindle Comic Converter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icons/comic2ebook.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name='Kindle Comic Converter',
)
app = BUNDLE(
    coll,
    name='Kindle Comic Converter.app',
    icon='icons/comic2ebook.icns',
    bundle_identifier=None,
)
