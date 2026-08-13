"""Small valid rigged-GLB fixture used only when no CUDA rigging provider is available."""

from __future__ import annotations

import struct
from pathlib import Path

from pygltflib import (
    ARRAY_BUFFER,
    ELEMENT_ARRAY_BUFFER,
    FLOAT,
    GLTF2,
    UNSIGNED_SHORT,
    Accessor,
    Asset,
    Attributes,
    Buffer,
    BufferView,
    Mesh,
    Node,
    Primitive,
    Scene,
    Skin,
)


def write_fixture_rigged_glb(path: Path) -> None:
    """Write a minimal skinned quad GLB with two joints and normalized weights.

    This is deliberately a fixture, never a substitute for a CUDA inference result.
    It gives the validation, review, and animation layers a standards-compliant rig
    while a real provider is unavailable.
    """
    positions = (
        (-0.5, 0.0, 0.0),
        (0.5, 0.0, 0.0),
        (-0.5, 1.0, 0.0),
        (0.5, 1.0, 0.0),
    )
    indices = (0, 1, 2, 2, 1, 3)
    joints = ((0, 0, 0, 0), (0, 0, 0, 0), (1, 0, 0, 0), (1, 0, 0, 0))
    weights = ((1.0, 0.0, 0.0, 0.0),) * 4
    inverse_bind = (
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    ) * 2
    chunks = (
        struct.pack("<12f", *(value for position in positions for value in position)),
        struct.pack("<6H", *indices),
        struct.pack("<16H", *(value for joint in joints for value in joint)),
        struct.pack("<16f", *(value for weight in weights for value in weight)),
        struct.pack("<32f", *inverse_bind),
    )
    blob, views = _pack_chunks(
        chunks, (ARRAY_BUFFER, ELEMENT_ARRAY_BUFFER, ARRAY_BUFFER, ARRAY_BUFFER, ARRAY_BUFFER)
    )
    gltf = GLTF2(
        asset=Asset(version="2.0", generator="Character Model Studio fixture rig"),
        scenes=[Scene(nodes=[0, 1])],
        scene=0,
        nodes=[
            Node(mesh=0, skin=0, name="FixtureMesh"),
            Node(children=[2], name="Root"),
            Node(translation=[0.0, 1.0, 0.0], name="Spine"),
        ],
        meshes=[
            Mesh(
                primitives=[
                    Primitive(
                        attributes=Attributes(POSITION=0, JOINTS_0=2, WEIGHTS_0=3),
                        indices=1,
                    )
                ]
            )
        ],
        skins=[Skin(inverseBindMatrices=4, skeleton=1, joints=[1, 2], name="FixtureSkin")],
        buffers=[Buffer(byteLength=len(blob))],
        bufferViews=views,
        accessors=[
            Accessor(
                bufferView=0,
                componentType=FLOAT,
                count=4,
                type="VEC3",
                min=[-0.5, 0.0, 0.0],
                max=[0.5, 1.0, 0.0],
            ),
            Accessor(bufferView=1, componentType=UNSIGNED_SHORT, count=6, type="SCALAR"),
            Accessor(bufferView=2, componentType=UNSIGNED_SHORT, count=4, type="VEC4"),
            Accessor(bufferView=3, componentType=FLOAT, count=4, type="VEC4"),
            Accessor(bufferView=4, componentType=FLOAT, count=2, type="MAT4"),
        ],
    )
    gltf.set_binary_blob(blob)
    path.parent.mkdir(parents=True, exist_ok=True)
    gltf.save_binary(path)


def _pack_chunks(
    chunks: tuple[bytes, ...], targets: tuple[int, ...]
) -> tuple[bytes, list[BufferView]]:
    blob = bytearray()
    views: list[BufferView] = []
    for chunk, target in zip(chunks, targets, strict=True):
        padding = (-len(blob)) % 4
        blob.extend(b"\x00" * padding)
        offset = len(blob)
        blob.extend(chunk)
        views.append(BufferView(buffer=0, byteOffset=offset, byteLength=len(chunk), target=target))
    return bytes(blob), views
