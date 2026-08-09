"""Real CUDA smoke test; intentionally never substitutes CPU execution."""

from __future__ import annotations

import json

import torch

from character_model_studio.app.capabilities import probe_runtime


def main() -> int:
    """Run a CUDA-resident tensor operation and emit runtime readiness diagnostics."""
    runtime = probe_runtime()
    if not runtime.gpu.cuda_available:
        print(json.dumps({"status": "BLOCKED_BY_ENVIRONMENT", "reason": "CUDA is unavailable"}))
        return 2
    device = torch.device("cuda:0")
    tensor = torch.arange(32, device=device, dtype=torch.float32)
    result = tensor.square().sum()
    torch.cuda.synchronize(device)
    if result.device.type != "cuda":
        raise RuntimeError("CUDA smoke result left the CUDA device")
    print(
        json.dumps(
            {
                "status": "PASS",
                "tier": runtime.tier,
                "cuda": runtime.gpu.cuda_available,
                "standard": runtime.standard.status,
                "segmentation": runtime.segmentation.status,
                "high_quality": runtime.high_quality.status,
                "rigging": runtime.rigging.status,
            },
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
