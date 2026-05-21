# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=['Lib/live_viewer'],
    binaries=[],
    datas=[
        ('Lib/live_viewer/nanji_drawing_new.png', '.'),
        ('Lib/live_viewer/nanji_2026_edited.png', '.'),
        ('settings', 'settings'),
    ],
    hiddenimports=[
        'main_window',
        'main_window_ui',
        'rendering_widget',
        'rendering_widget.rendering_dock',
        'rendering_widget.rendering_widget',
        'rendering_widget.rendering_view_ui',
        'rendering_widget.flat_push_button',
        'rendering_widget.resource_rc',
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
    [],
    exclude_binaries=True,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)
