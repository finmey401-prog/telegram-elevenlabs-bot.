import os

class Config:
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "your_bot_token_here")
    
    # Database Configuration
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///game.db")
    
    # Payment Configuration
    PAYMENT_PROVIDER_TOKEN = os.environ.get("PAYMENT_PROVIDER_TOKEN", "payment_token_here")
    
    # Game Configuration
    STARTING_COINS = 1000
    STARTING_ENERGY = 100
    MAX_ENERGY = 100
    ENERGY_REGEN_RATE = 1  # per minute
    
    # Business Configuration
    BUSINESS_TYPES = {
        'cafe': {'cost': 5000, 'income': 100, 'time': 3600},  # 1 hour
        'shop': {'cost': 15000, 'income': 300, 'time': 7200},  # 2 hours
        'factory': {'cost': 50000, 'income': 1000, 'time': 14400},  # 4 hours
        'bank': {'cost': 200000, 'income': 5000, 'time': 28800}  # 8 hours
    }
    
    # Farm Configuration
    CROPS = {
        'wheat': {'cost': 50, 'sell_price': 80, 'grow_time': 1800},  # 30 minutes
        'corn': {'cost': 100, 'sell_price': 160, 'grow_time': 3600},  # 1 hour
        'potato': {'cost': 200, 'sell_price': 320, 'grow_time': 7200},  # 2 hours
        'tomato': {'cost': 500, 'sell_price': 800, 'grow_time': 14400}  # 4 hours
    }
    
    # PvP Configuration
    ATTACK_COST = 50
    DEFENSE_COST = 100
    MIN_STEAL_PERCENTAGE = 5
    MAX_STEAL_PERCENTAGE = 15
    
    # VIP Configuration
    VIP_PRICES = {
        'basic': 299,  # rubles
        'premium': 599,
        'ultimate': 999
    }
    
    VIP_BENEFITS = {
        'basic': {'energy_bonus': 50, 'income_multiplier': 1.2, 'speed_boost': 1.1},
        'premium': {'energy_bonus': 100, 'income_multiplier': 1.5, 'speed_boost': 1.3},
        'ultimate': {'energy_bonus': 200, 'income_multiplier': 2.0, 'speed_boost': 1.5}
    }
    
    # Anti-cheat Configuration
    MAX_ACTIONS_PER_MINUTE = 10
    SUSPICIOUS_ACTIVITY_THRESHOLD = 50
    
    # Event Configuration
    DAILY_BONUS_AMOUNT = 500
    EVENT_FREQUENCY = 3600  # 1 hour between events
