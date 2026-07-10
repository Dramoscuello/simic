import os

import pytest

pytestmark = [pytest.mark.smoke_manual]


def _ensure_manual_run_enabled():
    if os.getenv("RUN_SMOKE_MANUAL") != "1":
        pytest.skip("Smoke manual deshabilitado. Use RUN_SMOKE_MANUAL=1.")


def _ensure_required_keys():
    required = ["OPENAI_API_KEY", "CLAUDE_API_KEY", "WOLFRAM_APP_ID"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        pytest.skip(f"Faltan variables para smoke manual: {', '.join(missing)}")


def test_smoke_manual_generation_ready():
    _ensure_manual_run_enabled()
    _ensure_required_keys()
    assert True


def test_smoke_manual_omr_ready():
    _ensure_manual_run_enabled()
    _ensure_required_keys()
    assert True
