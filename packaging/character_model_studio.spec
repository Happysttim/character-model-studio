# -*- mode: python ; coding: utf-8 -*-
"""One-folder recipe; model weights and user data stay outside this package."""

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

datas = []
binaries = []
hiddenimports = ["character_model_studio"]

for package in ("PySide6", "pyvista", "pyvistaqt", "vtkmodules", "trimesh", "pygltflib"):
    datas += collect_data_files(package)
    binaries += collect_dynamic_libs(package)
    hiddenimports += collect_submodules(package)

a = Analysis(
    ["src/character_model_studio/__main__.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="CharacterModelStudio", console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="CharacterModelStudio")
