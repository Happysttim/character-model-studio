"""User-actionable mapping for CUDA runtime failures."""

from __future__ import annotations


def map_cuda_error(error: BaseException) -> str:
    """Map CUDA OOM separately without masking unexpected failures."""
    message = str(error)
    if "out of memory" in message.lower():
        return (
            "CUDA ran out of memory. Close GPU-heavy apps or choose an eligible lower-memory mode."
        )
    return f"CUDA operation failed: {message}"
