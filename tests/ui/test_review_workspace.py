"""Review workspace and embedded viewport tests."""

from __future__ import annotations

import logging

from character_model_studio.app.bootstrap import ApplicationContext
from character_model_studio.platform.windows.paths import ApplicationPaths
from character_model_studio.ui.views.review import ReviewWorkspace
from character_model_studio.ui.views.workspace import definitions_by_key


def test_review_workspace_defers_native_viewport_until_activated(qtbot, tmp_path) -> None:
    root = tmp_path / "application-data"
    paths = ApplicationPaths(
        root, root / "logs", root / "Projects", root / "cache", root / "metadata.sqlite3"
    )
    workspace = ReviewWorkspace(
        ApplicationContext(paths=paths, logger=logging.getLogger(__name__)),
        definitions_by_key()["review"],
    )
    qtbot.addWidget(workspace)
    workspace.show()

    assert workspace._viewport is None
    assert workspace._initialized is False
