import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import threading
import time

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "telegram_bot_secret_key_2025")

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///game.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database
db.init_app(app)

def start_background_tasks():
    """Start background tasks for the game engine"""
    from events_system import EventsSystem
    from game_engine import GameEngine
    
    events_system = EventsSystem()
    game_engine = GameEngine()
    
    # Start event scheduler
    events_thread = threading.Thread(target=events_system.start_scheduler, daemon=True)
    events_thread.start()
    
    # Start game engine background tasks
    engine_thread = threading.Thread(target=game_engine.start_background_tasks, daemon=True)
    engine_thread.start()
    
    logger.info("Background tasks started")

if __name__ == '__main__':
    with app.app_context():
        # Import models to ensure tables are created
        import models  # noqa: F401
        
        # Create all database tables
        db.create_all()
        logger.info("Database tables created")
        
        # Start the Telegram bot
        from bot import TelegramBot
        
        bot = TelegramBot()
        
        # Start background tasks
        start_background_tasks()
        
        # Start the bot
        logger.info("Starting Telegram bot...")
        bot.start()
