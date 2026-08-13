"""Interactive local pose editor and lightweight From/To animation preview."""

from __future__ import annotations

from math import cos, radians, sin
from pathlib import Path
from typing import cast

from pygltflib import GLTF2
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from character_model_studio.animation.poses import PoseDocument, Quaternion, interpolate_pose
from character_model_studio.app.bootstrap import ApplicationContext
from character_model_studio.rigging.models import RigAttempt
from character_model_studio.ui.widgets.controls import PrimaryButton, SecondaryButton
from character_model_studio.ui.widgets.glass import GlassPanel
from character_model_studio.viewer.widget import ModelViewport


class AnimateWorkspace(QWidget):
    """Edit normalized local bone quaternions and persist a From/To clip."""

    def __init__(self, context: ApplicationContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._context = context
        self._rig: RigAttempt | None = None
        self._rotations: dict[str, Quaternion] = {}
        self._from_pose: PoseDocument | None = None
        self._to_pose: PoseDocument | None = None
        self._updating = False
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._advance_playback)
        self._build()

    def activate(self) -> None:
        """Load the newest validated rig and any persisted pose/clip state."""
        repository = self._context.repository
        if repository is None:
            return
        rigs = [
            rig
            for rig in repository.list_rig_attempts()
            if rig.rigged_relative_path and repository.rig_validation_status(rig.id) == "PASS"
        ]
        if not rigs:
            self._status.setText("No validated rig is available. Complete Rig first.")
            self._set_controls_enabled(False)
            return
        rig = rigs[0]
        if self._rig is not None and self._rig.id == rig.id:
            return
        self._rig = rig
        path = repository.projects_root / str(rig.rigged_relative_path)
        viewport = self._ensure_viewport()
        viewport.load_glb(path)
        viewport.set_skeleton_overlay(path, True)
        viewport.enable_skeleton_picking()
        viewport.skeleton_joint_picked.connect(self._pick_bone)
        bones = _bone_names(path)
        self._bone.clear()
        self._bone.addItems(bones)
        self._rotations = {bone: _identity() for bone in bones}
        self._restore_saved_state()
        self._set_controls_enabled(bool(bones))
        self._status.setText(f"Loaded validated rig with {len(bones)} editable bones.")
        self._sync_editor()

    def reset_loaded_rig(self) -> None:
        """Discard stale pose state when a different static GLB enters review."""
        self.stop_playback()
        self._rig = None
        self._rotations.clear()
        self._from_pose = None
        self._to_pose = None
        self._bone.clear()
        self._set_controls_enabled(False)
        self._status.setText("A new model was loaded. Complete Rig before editing animation.")

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        editor = GlassPanel("secondary", self)
        editor_layout = QVBoxLayout(editor)
        self._status = QLabel("Open a validated rig from the Rig tab.", editor)
        self._status.setWordWrap(True)
        self._bone = QComboBox(editor)
        self._bone.setObjectName("animationBoneSelector")
        self._bone.currentIndexChanged.connect(self._select_bone)
        editor_layout.addWidget(self._status)
        editor_layout.addWidget(QLabel("Selected bone", editor))
        editor_layout.addWidget(self._bone)
        self._angles: list[QDoubleSpinBox] = []
        for label in ("Local X°", "Local Y°", "Local Z°"):
            editor_layout.addWidget(QLabel(label, editor))
            spin = QDoubleSpinBox(editor)
            spin.setRange(-180.0, 180.0)
            spin.setSingleStep(2.0)
            spin.valueChanged.connect(self._apply_editor_rotation)
            self._angles.append(spin)
            editor_layout.addWidget(spin)
        pose_row = QHBoxLayout()
        for text, handler in (
            ("Save From", self.save_from),
            ("Save To", self.save_to),
            ("Reset pose", self.reset_pose),
            ("Swap", self.swap_poses),
        ):
            button = SecondaryButton(text, editor)
            button.clicked.connect(handler)
            pose_row.addWidget(button)
        editor_layout.addLayout(pose_row)
        self._duration = QSpinBox(editor)
        self._duration.setRange(100, 20000)
        self._duration.setValue(1000)
        self._duration.setSuffix(" ms")
        self._loop = QCheckBox("Loop preview", editor)
        self._loop.setChecked(True)
        self._timeline = QSlider(editor)
        self._timeline.setObjectName("animationTimeline")
        self._timeline.setOrientation(Qt.Orientation.Horizontal)
        self._timeline.setRange(0, 1000)
        self._timeline.valueChanged.connect(self._seek)
        timeline_row = QHBoxLayout()
        self._play = PrimaryButton("Play", editor)
        self._play.clicked.connect(self.toggle_playback)
        stop = SecondaryButton("Stop", editor)
        stop.clicked.connect(self.stop_playback)
        save = SecondaryButton("Save animation", editor)
        save.clicked.connect(self.save_animation)
        timeline_row.addWidget(self._play)
        timeline_row.addWidget(stop)
        timeline_row.addWidget(save)
        editor_layout.addWidget(QLabel("Duration", editor))
        editor_layout.addWidget(self._duration)
        editor_layout.addWidget(self._loop)
        editor_layout.addWidget(self._timeline)
        editor_layout.addLayout(timeline_row)
        editor_layout.addStretch(1)
        layout.addWidget(editor, stretch=2)
        viewer_panel = GlassPanel("secondary", self)
        viewer_layout = QVBoxLayout(viewer_panel)
        self._viewer_panel = viewer_panel
        self._viewer_layout = viewer_layout
        self._viewport: ModelViewport | None = None
        self._viewer_placeholder = QLabel(
            "Open a validated rig to prepare animation preview.", viewer_panel
        )
        self._viewer_placeholder.setWordWrap(True)
        viewer_layout.addWidget(self._viewer_placeholder, stretch=1)
        layout.addWidget(viewer_panel, stretch=5)
        self._set_controls_enabled(False)

    def _ensure_viewport(self) -> ModelViewport:
        """Create VTK only when the user actually opens a validated rig for editing."""
        if self._viewport is None:
            self._viewport = ModelViewport(self._viewer_panel)
            self._viewer_layout.addWidget(self._viewport, stretch=1)
            self._viewer_placeholder.hide()
        return self._viewport

    def _set_controls_enabled(self, enabled: bool) -> None:
        for widget in [
            self._bone,
            *self._angles,
            self._duration,
            self._loop,
            self._timeline,
            self._play,
        ]:
            widget.setEnabled(enabled)

    def _apply_editor_rotation(self) -> None:
        if self._updating or not self._bone.currentText():
            return
        values = [spin.value() for spin in self._angles]
        self._rotations[self._bone.currentText()] = _quaternion_from_euler(*values)
        self._status.setText("Local rotation updated. Save From or To to persist this pose.")

    def _sync_editor(self) -> None:
        if not self._bone.currentText():
            return
        self._updating = True
        # The editor starts at zero for each selected bone; storage remains quaternion-only.
        for spin in self._angles:
            spin.setValue(0.0)
        self._updating = False

    def _select_bone(self, index: int) -> None:
        """Synchronize the local editor and visibly mark the selected skeleton joint."""
        self._sync_editor()
        if self._viewport is None or self._rig is None or self._rig.rigged_relative_path is None:
            return
        repository = self._context.repository
        if repository is not None:
            self._viewport.select_skeleton_joint(
                repository.projects_root / self._rig.rigged_relative_path, index
            )

    def _pick_bone(self, index: int) -> None:
        """Apply a direct preview click to the same bone editor used by keyboard controls."""
        if 0 <= index < self._bone.count():
            self._bone.setCurrentIndex(index)

    def save_from(self) -> None:
        self._from_pose = self._current_pose()
        self._persist_pose("From", self._from_pose)
        self._status.setText("From pose saved.")

    def save_to(self) -> None:
        self._to_pose = self._current_pose()
        self._persist_pose("To", self._to_pose)
        self._status.setText("To pose saved.")

    def reset_pose(self) -> None:
        self._rotations = {name: _identity() for name in self._rotations}
        self._sync_editor()
        self._status.setText("Bind-pose rotations restored.")

    def swap_poses(self) -> None:
        self._from_pose, self._to_pose = self._to_pose, self._from_pose
        self._status.setText("From and To poses swapped.")

    def toggle_playback(self) -> None:
        if self._timer.isActive():
            self._timer.stop()
            self._play.setText("Play")
        elif self._from_pose is not None and self._to_pose is not None:
            self._timer.start()
            self._play.setText("Pause")
        else:
            self._status.setText("Save both From and To poses before playback.")

    def stop_playback(self) -> None:
        self._timer.stop()
        self._play.setText("Play")
        self._timeline.setValue(0)

    def _advance_playback(self) -> None:
        next_value = self._timeline.value() + round(33 * 1000 / self._duration.value())
        if next_value >= 1000:
            if self._loop.isChecked():
                next_value = 0
            else:
                self.stop_playback()
                return
        self._timeline.setValue(next_value)

    def _seek(self, value: int) -> None:
        if self._from_pose is None or self._to_pose is None:
            return
        pose = interpolate_pose(self._from_pose, self._to_pose, value / 1000)
        self._rotations.update(pose.bones)

    def save_animation(self) -> None:
        if self._rig is None or self._from_pose is None or self._to_pose is None:
            self._status.setText("Save From and To before saving the animation.")
            return
        repository = self._context.repository
        if repository is None:
            return
        repository.save_animation_clip(
            self._rig.id,
            "From-To",
            {
                "schemaVersion": 1,
                "durationMs": self._duration.value(),
                "loopPreview": self._loop.isChecked(),
                "from": self._from_pose.as_dict(),
                "to": self._to_pose.as_dict(),
            },
        )
        self._status.setText("Animation saved locally and will reopen with this rig.")

    def _persist_pose(self, name: str, pose: PoseDocument) -> None:
        if self._rig is not None and self._context.repository is not None:
            self._context.repository.save_pose_document(self._rig.id, name, pose.as_dict())

    def _restore_saved_state(self) -> None:
        if self._rig is None or self._context.repository is None:
            return
        poses = self._context.repository.load_pose_documents(self._rig.id)
        self._from_pose = _pose_from_payload(self._rig.id, poses.get("From"))
        self._to_pose = _pose_from_payload(self._rig.id, poses.get("To"))
        clip = self._context.repository.load_animation_clip(self._rig.id)
        if clip is not None:
            duration = clip.get("durationMs", 1000)
            self._duration.setValue(
                int(duration) if isinstance(duration, (int, float, str)) else 1000
            )
            self._loop.setChecked(bool(clip.get("loopPreview", True)))

    def _current_pose(self) -> PoseDocument:
        if self._rig is None:
            raise RuntimeError("No validated rig is loaded")
        return PoseDocument(self._rig.id, dict(self._rotations))


def _identity() -> Quaternion:
    return (0.0, 0.0, 0.0, 1.0)


def _quaternion_from_euler(x: float, y: float, z: float) -> Quaternion:
    """Convert UI edit angles to a normalized local quaternion for storage."""
    half_x, half_y, half_z = radians(x) / 2, radians(y) / 2, radians(z) / 2
    return (
        sin(half_x) * cos(half_y) * cos(half_z) - cos(half_x) * sin(half_y) * sin(half_z),
        cos(half_x) * sin(half_y) * cos(half_z) + sin(half_x) * cos(half_y) * sin(half_z),
        cos(half_x) * cos(half_y) * sin(half_z) - sin(half_x) * sin(half_y) * cos(half_z),
        cos(half_x) * cos(half_y) * cos(half_z) + sin(half_x) * sin(half_y) * sin(half_z),
    )


def _bone_names(path: Path) -> list[str]:
    gltf = GLTF2().load_binary(str(path))
    if not gltf.skins:
        return []
    return [gltf.nodes[index].name or f"bone_{index}" for index in gltf.skins[0].joints or []]


def _pose_from_payload(rig_id: str, payload: dict[str, object] | None) -> PoseDocument | None:
    if payload is None or not isinstance(payload.get("bones"), dict):
        return None
    raw_bones = cast(dict[object, object], payload["bones"])
    bones = {
        str(name): tuple(float(item) for item in value)
        for name, value in raw_bones.items()
        if isinstance(value, list) and len(value) == 4
    }
    return PoseDocument(rig_id, bones)  # type: ignore[arg-type]
