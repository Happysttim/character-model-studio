# -*- mode: python ; coding: utf-8 -*-
"""One-folder recipe; model weights and user data stay outside this package."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

project_root = Path(SPECPATH).parent

datas = []
binaries = []
hiddenimports = ["character_model_studio", "pyvistaqt"]

for package in ("pyvista", "pyvistaqt", "vtkmodules"):
    datas += collect_data_files(package)
    binaries += collect_dynamic_libs(package)

a = Analysis(
    [str(project_root / "src" / "character_model_studio" / "__main__.py")],
    pathex=[str(project_root / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="CharacterModelStudio", console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="CharacterModelStudio")
