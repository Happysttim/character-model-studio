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
    # PyInstaller executes an entry file as a top-level module.  The package's
    # ``__main__.py`` deliberately uses a relative import for ``python -m`` and
    # would therefore fail in a frozen top-level context.  This entry uses an
    # absolute package import instead.
    [str(project_root / "packaging" / "frozen_entry.py")],
    pathex=[str(project_root / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="CharacterModelStudio", console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="CharacterModelStudio")
