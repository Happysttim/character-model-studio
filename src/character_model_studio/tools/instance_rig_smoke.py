"""Check the isolated Instance-Rig runtime without allowing CPU auto-rigging."""

from __future__ import annotations

import json
import os
import subprocess

from character_model_studio.rigging.instance_rig_paths import resolve_instance_rig_paths


def main() -> int:
    """Report CUDA eligibility and local BodyPix availability for the optional provider."""
    paths = resolve_instance_rig_paths()
    model = paths.model_cache / "bodypix-resnet50-s16-480x640" / "saved_model.pb"
    if not paths.runtime_python.is_file():
        print(
            json.dumps({"status": "NOT_INSTALLED", "reason": "Isolated Python runtime is missing"})
        )
        return 2
    environment = os.environ.copy()
    environment["INSTANCERIG_CACHE_DIR"] = str(paths.model_cache)
    child = subprocess.run(
        [
            str(paths.runtime_python),
            "-E",
            "-c",
            "import json, tensorflow as tf; "
            "print(json.dumps({'tensorflow': tf.__version__, "
            "'gpu_devices': [device.name for device in tf.config.list_physical_devices('GPU')]}))",
        ],
        capture_output=True,
        check=False,
        env=environment,
        text=True,
    )
    if child.returncode:
        print(
            json.dumps({"status": "PROVIDER_RUNTIME_INCOMPATIBLE", "detail": child.stderr[-800:]})
        )
        return 2
    payload = json.loads(child.stdout.strip().splitlines()[-1])
    result = {
        "model_cache_present": model.is_file(),
        "model_bytes": model.stat().st_size if model.is_file() else 0,
        **payload,
    }
    if not result["gpu_devices"]:
        result["status"] = "BLOCKED_BY_ENVIRONMENT"
        result["reason"] = "TensorFlow CUDA device unavailable; CPU auto-rigging is disabled."
        print(json.dumps(result, sort_keys=True))
        return 2
    result["status"] = "READY_FOR_CUDA_INFERENCE"
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
