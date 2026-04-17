"""
WSGI entry point for LearnNova application
"""

import os
from app import create_app  # type: ignore[import]
from config import ProductionConfig

env = os.environ.get("FLASK_ENV", "production")

if env == "development":
    from config import DevelopmentConfig

    app = create_app(DevelopmentConfig)
else:
    app = create_app(ProductionConfig)
