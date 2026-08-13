"""CPU Linear Blend Skinning for a single glTF mesh primitive and skin."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from pygltflib import GLTF2

from character_model_studio.animation.poses import Quaternion


@dataclass(frozen=True, slots=True)
class SkinnedAsset:
    """Decoded glTF skin attributes separated from Qt/VTK rendering."""

    vertices: np.ndarray
    joint_indices: np.ndarray
    joint_weights: np.ndarray
    inverse_bind_matrices: np.ndarray
    base_joint_locals: np.ndarray
    parent_joints: tuple[int | None, ...]
    joint_names: tuple[str, ...]

    def deform(self, rotations: dict[str, Quaternion]) -> tuple[np.ndarray, np.ndarray]:
        """Apply local joint rotations and return deformed vertices and joint positions."""
        locals_ = self.base_joint_locals.copy()
        for index, name in enumerate(self.joint_names):
            rotation = rotations.get(name)
            if rotation is not None:
                locals_[index] = locals_[index] @ _quaternion_matrix(rotation)
        worlds = np.empty_like(locals_)
        for index, parent in enumerate(self.parent_joints):
            worlds[index] = locals_[index] if parent is None else worlds[parent] @ locals_[index]
        skin_matrices = worlds @ self.inverse_bind_matrices
        source = np.concatenate(
            (self.vertices, np.ones((len(self.vertices), 1), dtype=np.float64)), axis=1
        )
        transformed = np.zeros_like(source)
        for influence in range(self.joint_indices.shape[1]):
            matrices = skin_matrices[self.joint_indices[:, influence]]
            transformed += (
                np.einsum("nij,nj->ni", matrices, source)
                * self.joint_weights[:, influence, np.newaxis]
            )
        return transformed[:, :3], worlds[:, :3, 3]


def load_skinned_asset(path: Path) -> SkinnedAsset:
    """Decode POSITION, JOINTS_0, WEIGHTS_0 and inverse bind matrices from a GLB."""
    gltf = GLTF2().load_binary(str(path))
    if not gltf.skins:
        raise ValueError("The GLB has no skin")
    skin = gltf.skins[0]
    joint_nodes = list(skin.joints or [])
    if not joint_nodes or skin.inverseBindMatrices is None:
        raise ValueError("The GLB skin is missing joints or inverse bind matrices")
    primitive = _first_skinned_primitive(gltf)
    attributes = primitive.attributes
    if attributes is None or attributes.POSITION is None:
        raise ValueError("The skinned primitive is missing POSITION")
    if attributes.JOINTS_0 is None or attributes.WEIGHTS_0 is None:
        raise ValueError("The skinned primitive is missing JOINTS_0 or WEIGHTS_0")
    vertices = _accessor_array(gltf, attributes.POSITION).astype(np.float64)
    joint_indices = _accessor_array(gltf, attributes.JOINTS_0).astype(np.int64)
    joint_weights = _accessor_array(gltf, attributes.WEIGHTS_0).astype(np.float64)
    inverse_binds = _accessor_array(gltf, skin.inverseBindMatrices).astype(np.float64)
    if len(vertices) != len(joint_indices) or len(vertices) != len(joint_weights):
        raise ValueError("Skin accessor vertex counts do not match")
    if inverse_binds.shape != (len(joint_nodes), 16):
        raise ValueError("Inverse bind matrices do not match skin joints")
    if np.any(joint_indices < 0) or np.any(joint_indices >= len(joint_nodes)):
        raise ValueError("Skin joint index is outside the skin joint list")
    totals = joint_weights.sum(axis=1)
    if np.any(~np.isfinite(joint_weights)) or np.any(totals <= 1e-8):
        raise ValueError("Skin weights are invalid")
    joint_weights = joint_weights / totals[:, np.newaxis]
    parents = _node_parents(gltf)
    by_node = {node: index for index, node in enumerate(joint_nodes)}
    parent_joints = tuple(by_node.get(parents.get(node)) for node in joint_nodes)
    locals_ = np.stack([_node_matrix(gltf.nodes[node]) for node in joint_nodes])
    names = tuple(
        gltf.nodes[node].name or f"bone_{index}" for index, node in enumerate(joint_nodes)
    )
    return SkinnedAsset(
        vertices,
        joint_indices,
        joint_weights,
        inverse_binds.reshape((-1, 4, 4)).transpose((0, 2, 1)),
        locals_,
        parent_joints,
        names,
    )


def _first_skinned_primitive(gltf: GLTF2) -> Any:
    for mesh in gltf.meshes:
        for primitive in mesh.primitives:
            attributes = primitive.attributes
            if attributes is not None and attributes.JOINTS_0 is not None:
                return primitive
    raise ValueError("The GLB has no skinned mesh primitive")


def _accessor_array(gltf: GLTF2, index: int) -> np.ndarray:
    accessor = gltf.accessors[index]
    if accessor.bufferView is None:
        raise ValueError("Sparse/accessor-without-bufferView is not supported for skinning")
    component_type = {
        5120: np.int8,
        5121: np.uint8,
        5122: np.int16,
        5123: np.uint16,
        5125: np.uint32,
        5126: np.float32,
    }.get(accessor.componentType)
    components = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}.get(accessor.type)
    if component_type is None or components is None:
        raise ValueError("Unsupported glTF skin accessor type")
    view = gltf.bufferViews[accessor.bufferView]
    blob = gltf.binary_blob()
    if blob is None:
        raise ValueError("The GLB binary buffer is unavailable")
    offset = (view.byteOffset or 0) + (accessor.byteOffset or 0)
    stride = view.byteStride or np.dtype(component_type).itemsize * components
    if stride != np.dtype(component_type).itemsize * components:
        raise ValueError("Interleaved glTF skin accessors are not supported")
    array = np.frombuffer(
        blob, dtype=component_type, count=accessor.count * components, offset=offset
    )
    result = array.reshape((accessor.count, components))
    if accessor.normalized:
        maximum = {5120: 127, 5121: 255, 5122: 32767, 5123: 65535, 5125: 4294967295}.get(
            accessor.componentType
        )
        if maximum is None:
            raise ValueError("Normalized glTF accessor must use an integer component type")
        result = result.astype(np.float64) / maximum
    return result


def _node_parents(gltf: GLTF2) -> dict[int, int]:
    return {
        child: parent for parent, node in enumerate(gltf.nodes) for child in node.children or []
    }


def _node_matrix(node: Any) -> np.ndarray:
    if node.matrix:
        return np.asarray(node.matrix, dtype=np.float64).reshape((4, 4)).T
    translation = np.asarray(node.translation or [0.0, 0.0, 0.0], dtype=np.float64)
    scale = np.asarray(node.scale or [1.0, 1.0, 1.0], dtype=np.float64)
    matrix = _quaternion_matrix(tuple(node.rotation or [0.0, 0.0, 0.0, 1.0]))
    matrix[:3, :3] *= scale[np.newaxis, :]
    matrix[:3, 3] = translation
    return matrix


def _quaternion_matrix(value: tuple[float, float, float, float]) -> np.ndarray:
    x, y, z, w = value
    length = np.sqrt(x * x + y * y + z * z + w * w)
    if length <= 1e-12:
        raise ValueError("Joint quaternion cannot be zero")
    x, y, z, w = x / length, y / length, z / length, w / length
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0],
            [0, 0, 0, 1],
        ],
        dtype=np.float64,
    )
