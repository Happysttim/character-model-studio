"""Provider-adapter discovery report without loading model weights at startup."""

from __future__ import annotations

import json

from character_model_studio.app.capabilities import ProviderReadiness, probe_runtime


def main() -> int:
    """Report independent provider readiness in the active single-process runtime."""
    runtime = probe_runtime()
    print(
        json.dumps(
            {
                "standard": _readiness_dict(runtime.standard),
                "segmentation": _readiness_dict(runtime.segmentation),
                "high_quality": _readiness_dict(runtime.high_quality),
                "rigging": _readiness_dict(runtime.rigging),
            },
            default=str,
        )
    )
    return 0


def _readiness_dict(readiness: ProviderReadiness) -> dict[str, object]:
    return {
        "status": readiness.status,
        "reason": readiness.reason,
        "adapter_installed": readiness.adapter_installed,
        "vram_eligible": readiness.vram_eligible,
    }


if __name__ == "__main__":
    raise SystemExit(main())
