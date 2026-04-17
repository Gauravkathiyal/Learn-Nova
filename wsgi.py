"""
WSGI entry point for LearnNova application
"""

import os
from app import create_app # type: ignore[import]
from config import Config

app = create_app(Config)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
