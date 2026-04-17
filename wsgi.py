"""
WSGI entry point for LearnNova application
"""

import os
import sys

try:
    from app import create_app  # type: ignore[import]
    from config import ProductionConfig

    env = os.environ.get("FLASK_ENV", "production")

    if env == "development":
        from config import DevelopmentConfig

        app = create_app(DevelopmentConfig)
    else:
        app = create_app(ProductionConfig)
except Exception as e:
    print(f"Error loading app: {e}", file=sys.stderr)
    raise
