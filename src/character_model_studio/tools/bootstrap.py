"""Phase 01 local bootstrap command."""

from __future__ import annotations

import importlib.util
import json

from character_model_studio.app.bootstrap import create_application_context


def main() -> int:
    """Initialize safe local services and report provider installation state."""
    create_application_context()
    provider_modules = {
        "hunyuan3d_2": "hunyuan3d",
        "hunyuan3d_2_1": "hunyuan3d_2_1",
        "skintokens": "skintokens",
        "unirig": "unirig",
    }
    report = {
        "status": "PASS",
        "providers": {
            name: "INSTALLED" if importlib.util.find_spec(module) else "NOT_INSTALLED"
            for name, module in provider_modules.items()
        },
        "storage_initialized": True,
    }
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
