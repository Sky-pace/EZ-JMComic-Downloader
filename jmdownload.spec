# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app/main.py'],
    pathex=[],
    binaries=[],
    datas=[('config/option.yml', 'config')],
    hiddenimports=[
        'jmcomic',
        'jmcomic.api',
        'jmcomic.cl',
        'jmcomic.jm_client_impl',
        'jmcomic.jm_client_interface',
        'jmcomic.jm_config',
        'jmcomic.jm_downloader',
        'jmcomic.jm_entity',
        'jmcomic.jm_exception',
        'jmcomic.jm_option',
        'jmcomic.jm_plugin',
        'jmcomic.jm_toolkit',
    ],
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
    a.binaries,
    a.datas,
    [],
    name='jmdownload-v1.2.1',
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