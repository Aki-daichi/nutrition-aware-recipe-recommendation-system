import os
import glob
from pathlib import Path
from typing import Any

from .settings import get_settings


async def startup_models(app) -> None:
    settings = get_settings()
    cbf_model_path = Path(settings.CBF_MODEL_PATH)
    cf_model_path = Path(settings.CF_MODEL_PATH)

    # Import here to avoid heavy imports during module import time
    from .pipeline.cf import load_cf
    from .pipeline.cbf import load_cbf
    from .pipeline.nutrition import load_nutrition

    app.state.cf = load_cf(cf_model_path)

    # CBF artifacts may be absent in this capstone repo; allow startup and return
    # zero similarity scores in the CBF stage when missing.
    try:
        app.state.cbf = load_cbf(cbf_model_path)
    except FileNotFoundError:
        app.state.cbf = None

    app.state.nutrition = load_nutrition()


