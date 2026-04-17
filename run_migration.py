"""
Script to run database migration
"""
from app import create_app
from config import Config
from extensions import db
from models import Test

app = create_app(Config)

with app.app_context():
    # Create all tables
    db.create_all()
    print("Database tables created successfully!")
