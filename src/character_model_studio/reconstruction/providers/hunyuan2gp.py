"""Local, CUDA-only Hunyuan3D-2GP multi-view Shape + Texture provider."""

from __future__ import annotations

import gc
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import torch

from character_model_studio.app.capabilities import ProviderReadiness, ReadinessStatus, probe_runtime
from character_model_studio.common.cancellation import CancellationToken
from character_model_studio.reconstruction.hunyuan2gp_paths import resolve_hunyuan2gp_paths
from character_model_studio.reconstruction.interfaces import ReconstructionProvider


class Hunyuan3D2GPProvider(ReconstructionProvider):
    """Sequentially run local multi-view Shape then Delight/Paint texture on CUDA."""

    name = "Hunyuan3D-2GP"
    version = "upstream-local-experimental"

    def __init__(self) -> None:
        self._shape_pipeline: Any | None = None

    def probe(self) -> ProviderReadiness:
        return probe_runtime().hunyuan2gp

    def load(self) -> None:
        readiness = self.probe()
        if readiness.status is not ReadinessStatus.READY:
            raise RuntimeError(readiness.reason)
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is required; Hunyuan3D-2GP will not use a CPU fallback")
        paths = resolve_hunyuan2gp_paths()
        _configure_local_runtime(paths.source_directory, paths.model_cache)
        from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline  # type: ignore[import-not-found]

        self._shape_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            str(paths.shape_directory), variant="fp16", device="cuda:0"
        )
        devices = {str(parameter.device) for parameter in self._shape_pipeline.model.parameters()}
        if devices != {"cuda:0"}:
            self.unload()
            raise RuntimeError(f"Hunyuan3D-2GP Shape parameters are not CUDA-only: {sorted(devices)}")

    def unload(self) -> None:
        self._shape_pipeline = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def generate_shape(
        self, inputs: list[Path], output_path: Path, cancellation: CancellationToken,
        progress: Callable[[str, int, int], None] | None = None,
    ) -> Path:
        """Generate a textured GLB; four chronological isolated views are required."""
        if self._shape_pipeline is None:
            raise RuntimeError("Hunyuan3D-2GP is not loaded")
        if len(inputs) < 3:
            raise ValueError("Hunyuan3D-2GP requires at least three isolated multi-view frames")
        if cancellation.is_cancelled:
            raise RuntimeError("Hunyuan3D-2GP generation was cancelled before inference")
        from PIL import Image

        names = ("front", "left", "back", "right")
        images = {name: Image.open(path).convert("RGBA") for name, path in zip(names, inputs, strict=False)}
        if progress:
            progress("hunyuan2gp_shape", 0, 2)
        mesh = self._shape_pipeline(
            image=images, num_inference_steps=50, octree_resolution=384, num_chunks=8000,
            generator=torch.manual_seed(12345), output_type="trimesh",
        )[0]
        if cancellation.is_cancelled:
            raise RuntimeError("Hunyuan3D-2GP generation was cancelled before texture generation")
        if not len(mesh.vertices) or not len(mesh.faces):
            raise RuntimeError("Hunyuan3D-2GP returned an empty Shape mesh")
        shape_path = output_path.with_name("shape-before-texture.glb")
        shape_path.parent.mkdir(parents=True, exist_ok=True)
        mesh.export(shape_path)
        del mesh
        self.unload()
        if progress:
            progress("hunyuan2gp_shape", 1, 2)
            progress("hunyuan2gp_texture", 0, 2)
        _texture_local_mesh(shape_path, inputs[0], output_path)
        if progress:
            progress("hunyuan2gp_texture", 2, 2)
        return output_path


def _configure_local_runtime(source_directory: Path, model_cache: Path) -> None:
    """Configure source/cache paths before imports; inference is permanently offline."""
    if str(source_directory) not in sys.path:
        sys.path.insert(0, str(source_directory))
    os.environ["HY3DGEN_MODELS"] = str(model_cache.resolve())
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_MODULES_CACHE"] = str((model_cache / "modules-transformers-4.49").resolve())
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(Path(torch.__file__).parent / "lib"))


def _texture_local_mesh(shape_path: Path, reference: Path, output_path: Path) -> None:
    """Run Delight and Paint one at a time, never retaining both CUDA models together."""
    paths = resolve_hunyuan2gp_paths()
    _configure_local_runtime(paths.source_directory, paths.model_cache)
    import trimesh
    from PIL import Image
    from hy3dgen.texgen import Hunyuan3DPaintPipeline  # type: ignore[import-not-found]
    from hy3dgen.texgen.utils.uv_warp_utils import mesh_uv_wrap  # type: ignore[import-not-found]

    pipeline = Hunyuan3DPaintPipeline.from_pretrained(str(paths.delight_directory.parent))
    delight, paint = pipeline.models["delight_model"], pipeline.models["multiview_model"]
    delight.device = paint.device = "cuda:0"
    delight.pipeline.to("cuda:0")
    _require_cuda_parameters("Delight", delight.pipeline)
    image_prompt = delight(pipeline.recenter_image(Image.open(reference).convert("RGBA")))
    delight.pipeline.to("cpu")
    torch.cuda.empty_cache()
    mesh = mesh_uv_wrap(trimesh.load(shape_path, force="mesh"))
    pipeline.render.load_mesh(mesh)
    elevations, azimuths, weights = (pipeline.config.candidate_camera_elevs, pipeline.config.candidate_camera_azims, pipeline.config.candidate_view_weights)
    normal_maps = pipeline.render_normal_multiview(elevations, azimuths, use_abs_coor=True)
    position_maps = pipeline.render_position_multiview(elevations, azimuths)
    camera_info = [(((a // 30) + 9) % 12) // {-20: 1, 0: 1, 20: 1, -90: 3, 90: 3}[e] + {-20: 0, 0: 12, 20: 24, -90: 36, 90: 40}[e] for a, e in zip(azimuths, elevations, strict=True)]
    paint.pipeline.to("cuda:0")
    _require_cuda_parameters("Paint", paint.pipeline)
    multiviews = paint(image_prompt, normal_maps + position_maps, camera_info)
    paint.pipeline.to("cpu")
    torch.cuda.empty_cache()
    size = pipeline.config.render_size
    texture, mask = pipeline.bake_from_multiview([image.resize((size, size)) for image in multiviews], elevations, azimuths, weights, method=pipeline.config.merge_method)
    pipeline.render.set_texture(pipeline.texture_inpaint(texture, (mask.squeeze(-1).cpu().numpy() * 255).astype("uint8")))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pipeline.render.save_mesh().export(output_path)
    del pipeline
    gc.collect()
    torch.cuda.empty_cache()


def _require_cuda_parameters(name: str, pipeline: Any) -> None:
    devices = {str(parameter.device) for parameter in pipeline.components.values() if hasattr(parameter, "parameters") for parameter in parameter.parameters()}
    if not devices or any(not device.startswith("cuda:") for device in devices):
        raise RuntimeError(f"{name} parameters are not CUDA-only: {sorted(devices)}")
