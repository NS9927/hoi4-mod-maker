# PyInstaller spec — HOI4 MOD 制作工具打包配置.
# 用法: pyinstaller hoi4_map_maker.spec
# 产物: dist/HOI4MapMaker/HOI4MapMaker.exe

# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None


a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('data/atlas_tiles', 'data/atlas_tiles'),
    ],
    hiddenimports=[
        # features 是动态加载的, PyInstaller 抓不到, 显式列出
        'features.map.land',
        'features.map.province',
        'features.map.terrain',
        'features.map.height',
        'features.map.state',
        'features.map.country',
        'features.map.river',
        'features.map.continent',
        'features.content.tech_tree',
        'features.content.focus_tree',
        'features.content.events',
        'features.content.decisions',
        'features.content.characters',
        'features.content.portraits',
        'features.content.oob',
        'features.content.namelist',
        'features.content.flags',
        'features.content.ideas',
        'features.map.land.page',
        'features.map.province.page',
        'features.map.terrain.page',
        'features.map.height.page',
        'features.map.state.page',
        'features.map.country.page',
        'features.map.river.page',
        'features.map.land.renderer',
        'features.map.province.renderer',
        'features.map.terrain.renderer',
        'features.map.height.renderer',
        'features.map.state.renderer',
        'features.map.country.renderer',
        'features.map.river.renderer',
        'features.map.state.detail_dialog',
        'features.map.continent.dialog',
        'features.map.logistics',
        'features.map.logistics.page',
        'features.map.logistics.renderer',
        'features.map.strategic_region',
        'features.map.strategic_region.page',
        'features.map.colormap',
        'features.map.colormap.page',
        'features.map.default_map',
        'features.map.default_map.page',
        'scipy.ndimage',
        'scipy.spatial',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest', 'pytest_qt', 'tests',
        'torch', 'torchvision', 'torchaudio',
        'paddle', 'paddlepaddle',
        'cv2', 'opencv-python',
        'transformers', 'huggingface_hub',
        'onnxruntime', 'onnx',
        'llvmlite', 'numba',
        'av',
        'tensorflow', 'keras',
        'matplotlib', 'pandas',
        'IPython', 'jupyter', 'notebook',
        'tkinter',
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
    name='HOI4MapMaker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,     # 发布版不显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico' if os.path.exists('resources/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HOI4MapMaker',
)
