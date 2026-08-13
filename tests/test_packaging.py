"""Packaging-boundary checks that do not build a large Windows distribution."""

from __future__ import annotations

from pathlib import Path

import pytest

from character_model_studio.reconstruction.providers.hunyuan2gp import _resolve_texture_python


def test_packaging_recipe_keeps_model_cache_outside_distribution() -> None:
    recipe = Path("packaging/character_model_studio.spec").read_text(encoding="utf-8")

    assert "hunyuan3d" not in recipe.lower()
    assert "weights" in recipe.lower()


def test_frozen_entry_uses_an_absolute_package_import() -> None:
    """A PyInstaller script is top-level, so package-relative imports would fail."""
    entry = Path("packaging/frozen_entry.py").read_text(encoding="utf-8")

    assert "from character_model_studio.main import run" in entry
    assert "character_model_studio" in Path("packaging/character_model_studio.spec").read_text(
        encoding="utf-8"
    )
    assert "package-startup-error.log" in entry


def test_packaging_recipe_excludes_development_only_mypy_runtime() -> None:
    """PyVista's optional mypy plugin must not pull mypyc into the GUI EXE."""
    recipe = Path("packaging/character_model_studio.spec").read_text(encoding="utf-8")

    assert '"mypy"' in recipe
    assert "excludes=excludes" in recipe
    assert '"mypy_extensions"' not in recipe


def test_frozen_texture_lane_requires_explicit_child_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "character_model_studio.reconstruction.providers.hunyuan2gp.sys.frozen", True, raising=False
    )
    monkeypatch.delenv("CHARACTER_MODEL_STUDIO_HUNYUAN2GP_PYTHON", raising=False)

    with pytest.raises(RuntimeError, match="HUNYUAN2GP_PYTHON"):
        _resolve_texture_python()
