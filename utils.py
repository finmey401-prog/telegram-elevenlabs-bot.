import logging
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from main import app, db
from models import Player, Business, Farm, Transaction, PvPBattle, GameEvent
from config import Config

logger = logging.getLogger(__name__)

class TimeUtils:
    """Utility functions for time calculations and formatting"""
    
    @staticmethod
    def seconds_to_human_readable(seconds: int) -> str:
        """Convert seconds to human readable format"""
        if seconds < 60:
            return f"{seconds}с"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}м"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes > 0:
                return f"{hours}ч {minutes}м"
            return f"{hours}ч"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            if hours > 0:
                return f"{days}д {hours}ч"
            return f"{days}д"
    
    @staticmethod
    def get_time_until(target_time: datetime) -> int:
        """Get seconds until target time"""
        now = datetime.utcnow()
        if target_time <= now:
            return 0
        return int((target_time - now).total_seconds())
    
    @staticmethod
    def is_time_passed(target_time: datetime) -> bool:
        """Check if target time has passed"""
        return datetime.utcnow() >= target_time
    
    @staticmethod
    def add_time_to_now(**kwargs) -> datetime:
        """Add time to current datetime"""
        return datetime.utcnow() + timedelta(**kwargs)
    
    @staticmethod
    def get_day_start(date: datetime = None) -> datetime:
        """Get start of day (00:00:00)"""
        if date is None:
            date = datetime.utcnow()
        return datetime.combine(date.date(), datetime.min.time())
    
    @staticmethod
    def get_week_start(date: datetime = None) -> datetime:
        """Get start of week (Monday 00:00:00)"""
        if date is None:
            date = datetime.utcnow()
        days_since_monday = date.weekday()
        monday = date - timedelta(days=days_since_monday)
        return TimeUtils.get_day_start(monday)

class MathUtils:
    """Mathematical utility functions for game calculations"""
    
    @staticmethod
    def calculate_level_experience_requirement(level: int) -> int:
        """Calculate experience required for a specific level"""
        return level * 1000  # Linear progression: level * 1000 XP
    
    @staticmethod
    def calculate_total_experience_for_level(level: int) -> int:
        """Calculate total experience needed to reach a level"""
        return sum(MathUtils.calculate_level_experience_requirement(l) for l in range(1, level + 1))
    
    @staticmethod
    def calculate_level_from_experience(experience: int) -> Tuple[int, int]:
        """Calculate level and remaining experience from total experience"""
        level = 1
        remaining_exp = experience
        
        while remaining_exp >= MathUtils.calculate_level_experience_requirement(level):
            remaining_exp -= MathUtils.calculate_level_experience_requirement(level)
            level += 1
        
        return level, remaining_exp
    
    @staticmethod
    def calculate_compound_growth(initial_value: float, growth_rate: float, periods: int) -> float:
        """Calculate compound growth"""
        return initial_value * ((1 + growth_rate) ** periods)
    
    @staticmethod
    def calculate_percentage(value: float, total: float) -> float:
        """Calculate percentage safely"""
        if total == 0:
            return 0.0
        return round((value / total) * 100, 2)
    
    @staticmethod
    def random_gaussian(mean: float, std_dev: float, min_val: float = None, max_val: float = None) -> float:
        """Generate random number with gaussian distribution within bounds"""
        value = random.gauss(mean, std_dev)
        
        if min_val is not None:
            value = max(value, min_val)
        if max_val is not None:
            value = min(value, max_val)
            
        return value
    
    @staticmethod
    def interpolate(start: float, end: float, factor: float) -> float:
        """Linear interpolation between two values"""
        factor = max(0.0, min(1.0, factor))  # Clamp between 0 and 1
        return start + (end - start) * factor

class FormatUtils:
    """Utility functions for formatting data for display"""
    
    @staticmethod
    def format_number(number: int) -> str:
        """Format number with thousands separators"""
        return f"{number:,}"
    
    @staticmethod
    def format_large_number(number: int) -> str:
        """Format large numbers with K/M/B suffixes"""
        if number >= 1_000_000_000:
            return f"{number / 1_000_000_000:.1f}B"
        elif number >= 1_000_000:
            return f"{number / 1_000_000:.1f}M"
        elif number >= 1_000:
            return f"{number / 1_000:.1f}K"
        else:
            return str(number)
    
    @staticmethod
    def format_currency(amount: int, currency: str = "монет") -> str:
        """Format currency amount"""
        formatted_amount = FormatUtils.format_number(amount)
        return f"{formatted_amount} {currency}"
    
    @staticmethod
    def format_percentage(value: float) -> str:
        """Format percentage value"""
        return f"{value:.1f}%"
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%d.%m.%Y %H:%M") -> str:
        """Format datetime for display"""
        return dt.strftime(format_str)
    
    @staticmethod
    def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate string to max length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

class ValidationUtils:
    """Utility functions for data validation"""
    
    @staticmethod
    def is_valid_username(username: str) -> bool:
        """Validate username format"""
        if not username or len(username.strip()) == 0:
            return False
        if len(username) > 100:
            return False
        # Allow letters, numbers, underscores, and spaces
        import re
        return bool(re.match(r'^[a-zA-Zа-яА-Я0-9_\s]+$', username))
    
    @staticmethod
    def is_valid_amount(amount: int, min_val: int = 0, max_val: int = None) -> bool:
        """Validate amount is within bounds"""
        if amount < min_val:
            return False
        if max_val is not None and amount > max_val:
            return False
        return True
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input"""
        if not text:
            return ""
        # Remove potentially harmful characters
        import re
        cleaned = re.sub(r'[<>&"\'`]', '', text)
        return cleaned.strip()[:500]  # Limit length
    
    @staticmethod
    def validate_business_type(business_type: str) -> bool:
        """Validate business type exists in config"""
        return business_type in Config.BUSINESS_TYPES
    
    @staticmethod
    def validate_crop_type(crop_type: str) -> bool:
        """Validate crop type exists in config"""
        return crop_type in Config.CROPS

class GameMechanicsUtils:
    """Utility functions for game mechanics calculations"""
    
    @staticmethod
    def calculate_business_income_per_hour(business_type: str, level: int = 1) -> int:
        """Calculate business income per hour"""
        config = Config.BUSINESS_TYPES.get(business_type)
        if not config:
            return 0
        
        base_income = config['income'] * level
        time_per_collection = config['time']  # seconds
        collections_per_hour = 3600 / time_per_collection
        
        return int(base_income * collections_per_hour)
    
    @staticmethod
    def calculate_crop_profit(crop_type: str, quantity: int = 1) -> int:
        """Calculate profit from selling crops"""
        config = Config.CROPS.get(crop_type)
        if not config:
            return 0
        
        profit_per_crop = config['sell_price'] - config['cost']
        return profit_per_crop * quantity
    
    @staticmethod
    def calculate_roi_percentage(investment: int, returns: int, time_period_hours: int = 24) -> float:
        """Calculate Return on Investment percentage"""
        if investment <= 0:
            return 0.0
        
        profit = returns - investment
        roi = (profit / investment) * 100
        
        # Annualize ROI if time period is provided
        if time_period_hours != 8760:  # 8760 hours in a year
            roi = roi * (8760 / time_period_hours)
        
        return round(roi, 2)
    
    @staticmethod
    def calculate_player_wealth_score(player) -> int:
        """Calculate comprehensive wealth score for ranking"""
        base_score = player.coins
        
        # Add business value
        for business in player.businesses:
            business_config = Config.BUSINESS_TYPES.get(business.business_type, {})
            business_value = business_config.get('cost', 0) * business.level
            base_score += business_value
        
        # Add farm value
        for farm in player.farms:
            farm_value = 5000 * farm.level  # Base farm upgrade cost
            base_score += farm_value
        
        # Level bonus
        base_score += player.level * 1000
        
        return base_score
    
    @staticmethod
    def calculate_battle_power(player) -> float:
        """Calculate player's battle power for PvP"""
        # Base power from level
        base_power = player.level * 10
        
        # Power from wealth (logarithmic scaling)
        wealth_power = 0
        if player.coins > 1000:
            wealth_power = math.log10(player.coins / 1000) * 5
        
        # Power from businesses
        business_power = len(player.businesses) * 5
        
        # Power from farms
        farm_power = sum(farm.level * 3 for farm in player.farms)
        
        # Experience bonus
        exp_power = player.experience / 1000
        
        total_power = base_power + wealth_power + business_power + farm_power + exp_power
        
        # VIP multiplier
        if player.is_vip:
            vip_multipliers = {'basic': 1.1, 'premium': 1.2, 'ultimate': 1.3}
            multiplier = vip_multipliers.get(player.vip_type, 1.0)
            total_power *= multiplier
        
        return round(total_power, 2)

class DatabaseUtils:
    """Utility functions for database operations"""
    
    @staticmethod
    def get_or_create_player(user_id: int, username: str = None) -> Player:
        """Get existing player or create new one"""
        try:
            player = Player.query.filter_by(user_id=user_id).first()
            
            if not player:
                player = Player(
                    user_id=user_id,
                    username=username or f"Игрок_{user_id}",
                    coins=Config.STARTING_COINS,
                    energy=Config.STARTING_ENERGY
                )
                db.session.add(player)
                
                # Create initial farm
                farm = Farm(owner=player)
                db.session.add(farm)
                
                db.session.commit()
                logger.info(f"Created new player: {player.username} (ID: {user_id})")
            
            return player
            
        except Exception as e:
            logger.error(f"Error getting or creating player: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def safe_update_player_coins(player_id: int, amount: int, transaction_type: str, description: str) -> bool:
        """Safely update player coins with transaction logging"""
        try:
            player = Player.query.get(player_id)
            if not player:
                return False
            
            if transaction_type == "expense" and player.coins < amount:
                return False
            
            # Update coins
            if transaction_type == "income":
                player.coins += amount
                player.total_earned += amount
            elif transaction_type == "expense":
                player.coins -= amount
                player.total_spent += amount
            
            # Log transaction
            transaction = Transaction(
                player_id=player_id,
                transaction_type=transaction_type,
                amount=amount,
                description=description
            )
            db.session.add(transaction)
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating player coins: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_top_players_by_metric(metric: str, limit: int = 10) -> List[Dict]:
        """Get top players by specified metric"""
        try:
            if metric == "coins":
                players = Player.query.order_by(Player.coins.desc()).limit(limit).all()
                return [{"player": p, "score": p.coins} for p in players]
            elif metric == "level":
                players = Player.query.order_by(Player.level.desc(), Player.experience.desc()).limit(limit).all()
                return [{"player": p, "score": p.level} for p in players]
            elif metric == "pvp_wins":
                players = Player.query.order_by(Player.pvp_wins.desc()).limit(limit).all()
                return [{"player": p, "score": p.pvp_wins} for p in players]
            elif metric == "wealth":
                players = Player.query.all()
                wealthy_players = sorted(
                    players, 
                    key=lambda p: GameMechanicsUtils.calculate_player_wealth_score(p), 
                    reverse=True
                )[:limit]
                return [{"player": p, "score": GameMechanicsUtils.calculate_player_wealth_score(p)} for p in wealthy_players]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting top players: {e}")
            return []
    
    @staticmethod
    def cleanup_expired_data(days_old: int = 30) -> int:
        """Clean up old data from database"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Delete old transactions
            deleted_transactions = Transaction.query.filter(
                Transaction.created_at < cutoff_date
            ).delete()
            
            # Delete old player activities
            from models import PlayerActivity
            deleted_activities = PlayerActivity.query.filter(
                PlayerActivity.timestamp < cutoff_date
            ).delete()
            
            # Delete old PvP battles
            deleted_battles = PvPBattle.query.filter(
                PvPBattle.created_at < cutoff_date
            ).delete()
            
            db.session.commit()
            
            total_deleted = deleted_transactions + deleted_activities + deleted_battles
            logger.info(f"Cleaned up {total_deleted} old records")
            
            return total_deleted
            
        except Exception as e:
            logger.error(f"Error cleaning up expired data: {e}")
            db.session.rollback()
            return 0

class RandomUtils:
    """Utility functions for randomization with game balance"""
    
    @staticmethod
    def weighted_random_choice(choices: List[Tuple[Any, float]]) -> Any:
        """Choose random item based on weights"""
        if not choices:
            return None
        
        total_weight = sum(weight for _, weight in choices)
        random_weight = random.uniform(0, total_weight)
        
        current_weight = 0
        for item, weight in choices:
            current_weight += weight
            if random_weight <= current_weight:
                return item
        
        return choices[-1][0]  # Fallback to last item
    
    @staticmethod
    def random_event_outcome(base_chance: float, luck_modifier: float = 0.0) -> bool:
        """Calculate random outcome with luck modifier"""
        final_chance = max(0.0, min(1.0, base_chance + luck_modifier))
        return random.random() < final_chance
    
    @staticmethod
    def random_range_weighted(min_val: int, max_val: int, weight_towards_center: bool = True) -> int:
        """Generate random number in range with optional center weighting"""
        if not weight_towards_center:
            return random.randint(min_val, max_val)
        
        # Use triangular distribution weighted towards center
        center = (min_val + max_val) / 2
        return int(random.triangular(min_val, max_val, center))
    
    @staticmethod
    def generate_daily_seed() -> int:
        """Generate consistent daily seed for reproducible randomness"""
        today = datetime.utcnow().date()
        return hash(today.isoformat()) % 2147483647

class ConfigUtils:
    """Utility functions for configuration management"""
    
    @staticmethod
    def get_business_config(business_type: str) -> Dict:
        """Get business configuration safely"""
        return Config.BUSINESS_TYPES.get(business_type, {})
    
    @staticmethod
    def get_crop_config(crop_type: str) -> Dict:
        """Get crop configuration safely"""
        return Config.CROPS.get(crop_type, {})
    
    @staticmethod
    def get_vip_benefits(vip_type: str) -> Dict:
        """Get VIP benefits safely"""
        return Config.VIP_BENEFITS.get(vip_type, {})
    
    @staticmethod
    def calculate_dynamic_pricing(base_price: int, demand_factor: float = 1.0, supply_factor: float = 1.0) -> int:
        """Calculate dynamic pricing based on supply and demand"""
        # Simple supply and demand pricing
        price_multiplier = demand_factor / supply_factor
        
        # Cap the multiplier to prevent extreme prices
        price_multiplier = max(0.5, min(2.0, price_multiplier))
        
        return int(base_price * price_multiplier)

class NotificationUtils:
    """Utility functions for game notifications and messages"""
    
    @staticmethod
    def create_level_up_message(old_level: int, new_level: int, reward: int) -> str:
        """Create level up notification message"""
        return (
            f"🎉 <b>Поздравляем с повышением уровня!</b>\n\n"
            f"Уровень: {old_level} → {new_level}\n"
            f"Награда: {FormatUtils.format_currency(reward)}\n\n"
            f"Ваши возможности расширились!"
        )
    
    @staticmethod
    def create_business_ready_message(business_type: str, income: int) -> str:
        """Create business income ready message"""
        business_emoji = {
            'cafe': '☕',
            'shop': '🏪',
            'factory': '🏭',
            'bank': '🏦'
        }
        
        emoji = business_emoji.get(business_type, '🏢')
        return f"{emoji} Ваш {business_type} готов! Доход: {FormatUtils.format_currency(income)}"
    
    @staticmethod
    def create_crop_ready_message(crop_type: str) -> str:
        """Create crop harvest ready message"""
        crop_emoji = {
            'wheat': '🌾',
            'corn': '🌽',
            'potato': '🥔',
            'tomato': '🍅'
        }
        
        emoji = crop_emoji.get(crop_type, '🌱')
        return f"{emoji} Ваш урожай {crop_type} готов к сбору!"
    
    @staticmethod
    def create_pvp_result_message(is_winner: bool, opponent: str, amount: int) -> str:
        """Create PvP battle result message"""
        if is_winner:
            return (
                f"⚔️ <b>Победа в бою!</b>\n\n"
                f"Противник: {opponent}\n"
                f"Украдено: {FormatUtils.format_currency(amount)}\n"
                f"🏆 Ваша репутация растет!"
            )
        else:
            return (
                f"🛡️ <b>Защита успешна!</b>\n\n"
                f"Атакующий: {opponent}\n"
                f"Потери: {FormatUtils.format_currency(amount)}\n"
                f"💪 Укрепите свою оборону!"
            )

# Global utility instances for easy access
time_utils = TimeUtils()
math_utils = MathUtils()
format_utils = FormatUtils()
validation_utils = ValidationUtils()
game_utils = GameMechanicsUtils()
db_utils = DatabaseUtils()
random_utils = RandomUtils()
config_utils = ConfigUtils()
notification_utils = NotificationUtils()

def get_player_summary(player) -> Dict[str, Any]:
    """Get comprehensive player summary for display"""
    return {
        'basic_info': {
            'username': player.username,
            'level': player.level,
            'coins': player.coins,
            'energy': player.energy,
            'experience': player.experience
        },
        'businesses': len(player.businesses),
        'farms': len(player.farms),
        'pvp_record': {
            'wins': player.pvp_wins,
            'losses': player.pvp_losses,
            'win_rate': MathUtils.calculate_percentage(player.pvp_wins, player.pvp_wins + player.pvp_losses)
        },
        'wealth_score': GameMechanicsUtils.calculate_player_wealth_score(player),
        'battle_power': GameMechanicsUtils.calculate_battle_power(player),
        'vip_status': {
            'is_vip': player.is_vip,
            'type': player.vip_type,
            'expires_at': player.vip_expires_at
        }
    }

def log_game_action(action: str, player_id: int, details: Dict[str, Any] = None):
    """Log game action for analytics and debugging"""
    try:
        logger.info(f"Game Action: {action} by player {player_id} - {details}")
    except Exception as e:
        logger.error(f"Error logging game action: {e}")

def check_and_notify_achievements(player) -> List[str]:
    """Check for new achievements and return notification messages"""
    achievements = []
    
    # Level milestones
    if player.level in [5, 10, 25, 50, 100]:
        achievements.append(f"🎯 Достижение разблокировано: Уровень {player.level}!")
    
    # Wealth milestones
    wealth_milestones = [10000, 50000, 100000, 500000, 1000000]
    for milestone in wealth_milestones:
        if player.coins >= milestone:
            achievements.append(f"💰 Достижение разблокировано: {FormatUtils.format_large_number(milestone)} монет!")
    
    # Business achievements
    business_count = len(player.businesses)
    if business_count in [1, 5, 10, 25]:
        achievements.append(f"🏢 Достижение разблокировано: {business_count} бизнесов!")
    
    # PvP achievements
    if player.pvp_wins in [1, 10, 50, 100]:
        achievements.append(f"⚔️ Достижение разблокировано: {player.pvp_wins} побед в PvP!")
    
    return achievements

def calculate_server_statistics() -> Dict[str, Any]:
    """Calculate comprehensive server statistics"""
    try:
        with app.app_context():
            total_players = Player.query.count()
            active_today = Player.query.filter(
                Player.last_energy_update >= TimeUtils.get_day_start()
            ).count()
            
            total_businesses = Business.query.count()
            total_farms = Farm.query.count()
            total_coins = db.session.query(db.func.sum(Player.coins)).scalar() or 0
            
            return {
                'players': {
                    'total': total_players,
                    'active_today': active_today,
                    'activity_rate': MathUtils.calculate_percentage(active_today, total_players)
                },
                'economy': {
                    'total_coins': total_coins,
                    'total_businesses': total_businesses,
                    'total_farms': total_farms,
                    'average_wealth': total_coins // max(1, total_players)
                },
                'timestamp': datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Error calculating server statistics: {e}")
        return {}
