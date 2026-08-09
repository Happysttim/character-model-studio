"""Real CUDA smoke test for the local character-isolation provider."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw

from character_model_studio.app.bootstrap import create_application_context
from character_model_studio.reconstruction.providers.rembg_segmentation import (
    RembgAnimeSegmentationProvider,
)


def main() -> int:
    """Run one local CUDA segmentation operation without retaining image content."""
    create_application_context()
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = root / "source.png"
        foreground = root / "foreground.png"
        mask = root / "mask.png"
        _write_generated_fixture(source)
        provider = RembgAnimeSegmentationProvider()
        provider.load()
        try:
            provider.isolate(source, foreground, mask)
        finally:
            provider.unload()
        with Image.open(mask) as mask_image:
            alpha_range = mask_image.getextrema()
        if alpha_range is None or alpha_range[1] == 0:
            raise RuntimeError("Segmentation smoke produced an empty alpha mask")
        print(
            {
                "status": "PASS",
                "provider": provider.name,
                "model": provider.model_name,
                "foreground_bytes": foreground.stat().st_size,
                "mask_bytes": mask.stat().st_size,
                "alpha_range": alpha_range,
            }
        )
    return 0


def _write_generated_fixture(path: Path) -> None:
    """Create a non-user synthetic foreground fixture for provider smoke coverage."""
    image = Image.new("RGB", (512, 512), "#758F94")
    painter = ImageDraw.Draw(image)
    painter.ellipse((176, 58, 336, 218), fill="#E9B08A")
    painter.rounded_rectangle((152, 190, 360, 455), radius=72, fill="#243047")
    image.save(path)


if __name__ == "__main__":
    raise SystemExit(main())
