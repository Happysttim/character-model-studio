# -*- mode: python ; coding: utf-8 -*-
"""One-folder recipe; model weights and user data stay outside this package."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

project_root = Path(SPECPATH).parent

datas = []
binaries = []
hiddenimports = ["character_model_studio", "pyvistaqt"]
# PyVista exposes a static-type plugin which conditionally imports mypy when it
# happens to be installed in the build environment.  mypy's randomized mypyc
# extension name is not a runtime application dependency and can be omitted by
# PyInstaller, causing a windowed EXE to fail during import.  Keep every
# development-only checker out of the frozen runtime so PyVista sees no mypy.
excludes = ["mypy", "pytest", "pytestqt", "coverage", "ruff"]

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
    excludes=excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="CharacterModelStudio", console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="CharacterModelStudio")
