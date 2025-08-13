import time
import logging
from datetime import datetime, timedelta
from main import app, db
from models import Player, Business, Farm, Transaction, GameEvent, Leaderboard
from config import Config
import threading

logger = logging.getLogger(__name__)

class GameEngine:
    def __init__(self):
        self.running = True
        
    def start_background_tasks(self):
        """Start all background game engine tasks"""
        logger.info("Starting game engine background tasks...")
        
        while self.running:
            try:
                with app.app_context():
                    self.update_player_energy()
                    self.process_business_income()
                    self.update_leaderboards()
                    self.cleanup_old_data()
                
                # Sleep for 60 seconds between updates
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in game engine background tasks: {e}")
                time.sleep(10)  # Short sleep on error
    
    def update_player_energy(self):
        """Update energy for all players"""
        try:
            players = Player.query.all()
            
            for player in players:
                old_energy = player.energy
                player.update_energy()
                
                if player.energy != old_energy:
                    db.session.add(player)
            
            db.session.commit()
            logger.debug(f"Updated energy for {len(players)} players")
            
        except Exception as e:
            logger.error(f"Error updating player energy: {e}")
            db.session.rollback()
    
    def process_business_income(self):
        """Process automatic business income updates"""
        try:
            businesses = Business.query.all()
            
            for business in businesses:
                # Update last collection time for businesses that have been idle
                business_config = Config.BUSINESS_TYPES.get(business.business_type)
                if not business_config:
                    continue
                
                # Check if business should auto-collect (for idle gameplay)
                time_since_collection = (datetime.utcnow() - business.last_collection).total_seconds()
                collection_interval = business_config['time']
                
                # Auto-collect if 10 intervals have passed (prevents infinite accumulation)
                if time_since_collection >= collection_interval * 10:
                    income = business_config['income'] * business.level
                    
                    # Apply VIP multiplier
                    if business.owner.is_vip and business.owner.vip_type in Config.VIP_BENEFITS:
                        multiplier = Config.VIP_BENEFITS[business.owner.vip_type]['income_multiplier']
                        income = int(income * multiplier)
                    
                    business.owner.coins += income
                    business.owner.total_earned += income
                    business.last_collection = datetime.utcnow()
                    
                    # Add transaction record
                    transaction = Transaction(
                        player_id=business.owner.id,
                        transaction_type="income",
                        amount=income,
                        description=f"Автосбор с {business.business_type}"
                    )
                    db.session.add(transaction)
            
            db.session.commit()
            logger.debug(f"Processed income for {len(businesses)} businesses")
            
        except Exception as e:
            logger.error(f"Error processing business income: {e}")
            db.session.rollback()
    
    def update_leaderboards(self):
        """Update leaderboard rankings"""
        try:
            # Clear existing leaderboard
            Leaderboard.query.delete()
            
            # Coins leaderboard
            top_coins = Player.query.order_by(Player.coins.desc()).limit(100).all()
            for rank, player in enumerate(top_coins, 1):
                leaderboard_entry = Leaderboard(
                    player_id=player.id,
                    category="coins",
                    score=player.coins,
                    rank=rank
                )
                db.session.add(leaderboard_entry)
            
            # Level leaderboard
            top_levels = Player.query.order_by(Player.level.desc(), Player.experience.desc()).limit(100).all()
            for rank, player in enumerate(top_levels, 1):
                leaderboard_entry = Leaderboard(
                    player_id=player.id,
                    category="level",
                    score=player.level,
                    rank=rank
                )
                db.session.add(leaderboard_entry)
            
            # PvP wins leaderboard
            top_pvp = Player.query.order_by(Player.pvp_wins.desc()).limit(100).all()
            for rank, player in enumerate(top_pvp, 1):
                leaderboard_entry = Leaderboard(
                    player_id=player.id,
                    category="pvp_wins",
                    score=player.pvp_wins,
                    rank=rank
                )
                db.session.add(leaderboard_entry)
            
            db.session.commit()
            logger.debug("Updated leaderboards")
            
        except Exception as e:
            logger.error(f"Error updating leaderboards: {e}")
            db.session.rollback()
    
    def cleanup_old_data(self):
        """Clean up old transaction records and activity logs"""
        try:
            # Keep only last 30 days of transactions
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            old_transactions = Transaction.query.filter(
                Transaction.created_at < cutoff_date
            ).delete()
            
            # Keep only last 7 days of player activities
            from models import PlayerActivity
            activity_cutoff = datetime.utcnow() - timedelta(days=7)
            
            old_activities = PlayerActivity.query.filter(
                PlayerActivity.timestamp < activity_cutoff
            ).delete()
            
            db.session.commit()
            
            if old_transactions > 0 or old_activities > 0:
                logger.info(f"Cleaned up {old_transactions} old transactions and {old_activities} old activities")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            db.session.rollback()
    
    def calculate_level_up(self, player):
        """Calculate if player should level up"""
        experience_needed = player.level * 1000  # Each level needs level * 1000 XP
        
        if player.experience >= experience_needed:
            player.level += 1
            player.experience -= experience_needed
            
            # Level up rewards
            level_reward = player.level * 100
            player.coins += level_reward
            
            # Add transaction
            transaction = Transaction(
                player_id=player.id,
                transaction_type="income",
                amount=level_reward,
                description=f"Награда за достижение {player.level} уровня"
            )
            db.session.add(transaction)
            
            return True
        
        return False
    
    def add_experience(self, player, amount):
        """Add experience to player and check for level up"""
        player.experience += amount
        
        leveled_up = False
        # Check for multiple level ups
        while self.calculate_level_up(player):
            leveled_up = True
        
        return leveled_up
    
    def calculate_business_upgrade_cost(self, business):
        """Calculate cost to upgrade business"""
        base_cost = Config.BUSINESS_TYPES[business.business_type]['cost']
        upgrade_cost = int(base_cost * (business.level * 0.5))
        return upgrade_cost
    
    def upgrade_business(self, business, player):
        """Upgrade business to next level"""
        upgrade_cost = self.calculate_business_upgrade_cost(business)
        
        if player.coins < upgrade_cost:
            return False, "Недостаточно монет для улучшения"
        
        if player.energy < 20:
            return False, "Недостаточно энергии для улучшения"
        
        # Perform upgrade
        player.coins -= upgrade_cost
        player.energy -= 20
        player.total_spent += upgrade_cost
        business.level += 1
        
        # Add experience
        self.add_experience(player, 50)
        
        # Add transaction
        transaction = Transaction(
            player_id=player.id,
            transaction_type="expense",
            amount=upgrade_cost,
            description=f"Улучшение {business.business_type} до {business.level} уровня"
        )
        db.session.add(transaction)
        
        return True, f"Бизнес улучшен до {business.level} уровня!"
    
    def calculate_farm_upgrade_cost(self, farm):
        """Calculate cost to upgrade farm"""
        base_cost = 5000
        upgrade_cost = int(base_cost * (farm.level * 0.8))
        return upgrade_cost
    
    def upgrade_farm(self, farm, player):
        """Upgrade farm to next level (more slots)"""
        upgrade_cost = self.calculate_farm_upgrade_cost(farm)
        
        if player.coins < upgrade_cost:
            return False, "Недостаточно монет для улучшения"
        
        if player.energy < 30:
            return False, "Недостаточно энергии для улучшения"
        
        # Perform upgrade
        player.coins -= upgrade_cost
        player.energy -= 30
        player.total_spent += upgrade_cost
        farm.level += 1
        farm.slots += 2  # Add 2 more slots per level
        
        # Add experience
        self.add_experience(player, 75)
        
        # Add transaction
        transaction = Transaction(
            player_id=player.id,
            transaction_type="expense",
            amount=upgrade_cost,
            description=f"Улучшение фермы до {farm.level} уровня"
        )
        db.session.add(transaction)
        
        return True, f"Ферма улучшена до {farm.level} уровня! Слотов: {farm.slots}"
    
    def stop(self):
        """Stop the game engine"""
        self.running = False
        logger.info("Game engine stopped")
