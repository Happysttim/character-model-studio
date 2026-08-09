"""Real CUDA smoke test for a fully local Stable Fast 3D installation."""

from __future__ import annotations

import gc
import json
import os
import sys
from contextlib import suppress
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml  # type: ignore[import-untyped]
from PIL import Image, ImageDraw

from character_model_studio.platform.windows.paths import resolve_application_paths
from character_model_studio.validation.model import ModelValidator

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    """Generate and validate one textured GLB using only local CUDA model files."""
    _configure_offline_runtime()
    model_directory, dino_directory, source_directory = _resolve_paths()
    _require_local_files(model_directory, dino_directory, source_directory)
    sys.path.insert(0, str(source_directory))

    import torch
    from sf3d.system import SF3D  # type: ignore[import-not-found]

    if not torch.cuda.is_available():
        raise RuntimeError("SF3D smoke requires a CUDA device; CPU fallback is not permitted")

    with TemporaryDirectory(dir=model_directory.parent) as temporary:
        root = Path(temporary)
        runtime_model_directory = _write_runtime_config(root, model_directory, dino_directory)
        source_image = root / "source.png"
        output_path = root / "textured.glb"
        _write_rgba_fixture(source_image)
        free_before, total = torch.cuda.mem_get_info()
        torch.cuda.reset_peak_memory_stats()
        model = SF3D.from_pretrained(
            str(runtime_model_directory), config_name="config.yaml", weight_name="model.safetensors"
        )
        model.to("cuda")
        model.eval()
        parameter_device = str(next(model.parameters()).device)
        try:
            with (
                Image.open(source_image) as image,
                torch.no_grad(),
                torch.autocast(device_type="cuda", dtype=torch.bfloat16),
            ):
                mesh, _ = model.run_image(image.convert("RGBA"), bake_resolution=256, remesh="none")
            mesh.export(output_path, include_normals=True)
            report = ModelValidator().validate(output_path)
            if not output_path.is_file() or output_path.stat().st_size == 0:
                raise RuntimeError("SF3D smoke did not write a textured GLB")
            result = {
                "status": "PASS",
                "provider": "Stable Fast 3D",
                "parameter_device": parameter_device,
                "free_vram_before_bytes": free_before,
                "total_vram_bytes": total,
                "peak_allocated_vram_bytes": torch.cuda.max_memory_allocated(),
                "vertices": len(mesh.vertices),
                "faces": len(mesh.faces),
                "glb_bytes": output_path.stat().st_size,
                "validation": report.as_dict(),
            }
            print(json.dumps(result, default=str))
        finally:
            del model
            gc.collect()
            with suppress(RuntimeError):
                torch.cuda.empty_cache()
    return 0


def _configure_offline_runtime() -> None:
    paths = resolve_application_paths()
    os.environ.setdefault("HF_HOME", str(paths.cache_directory / "huggingface"))
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"


def _resolve_paths() -> tuple[Path, Path, Path]:
    paths = resolve_application_paths()
    cache = paths.cache_directory / "sf3d"
    return (
        Path(os.environ.get("CHARACTER_MODEL_STUDIO_SF3D_MODEL_DIR", cache / "stable-fast-3d")),
        Path(os.environ.get("CHARACTER_MODEL_STUDIO_SF3D_DINO_DIR", cache / "dinov2-large")),
        Path(
            os.environ.get(
                "CHARACTER_MODEL_STUDIO_SF3D_SOURCE_DIR", PROJECT_ROOT / "external" / "StableFast3D"
            )
        ),
    )


def _require_local_files(
    model_directory: Path, dino_directory: Path, source_directory: Path
) -> None:
    required = (
        model_directory / "config.yaml",
        model_directory / "model.safetensors",
        dino_directory / "config.json",
        dino_directory / "model.safetensors",
        source_directory / "sf3d" / "system.py",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"Local SF3D smoke prerequisites are missing: {missing}")


def _write_runtime_config(root: Path, model_directory: Path, dino_directory: Path) -> Path:
    config = yaml.safe_load((model_directory / "config.yaml").read_text(encoding="utf-8"))
    config["image_tokenizer"]["pretrained_model_name_or_path"] = str(dino_directory)
    runtime_directory = root / "model"
    runtime_directory.mkdir()
    (runtime_directory / "config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )
    (runtime_directory / "model.safetensors").hardlink_to(model_directory / "model.safetensors")
    return runtime_directory


def _write_rgba_fixture(path: Path) -> None:
    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    painter = ImageDraw.Draw(image)
    painter.ellipse((178, 64, 334, 220), fill="#E9B08A")
    painter.rounded_rectangle((154, 190, 358, 450), radius=70, fill="#243047")
    painter.polygon(((154, 265), (84, 448), (202, 410)), fill="#A55447")
    image.save(path)


if __name__ == "__main__":
    raise SystemExit(main())
