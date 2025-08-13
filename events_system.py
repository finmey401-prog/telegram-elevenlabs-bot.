import logging
import random
import time
import threading
from datetime import datetime, timedelta
from main import app, db
from models import Player, GameEvent, Transaction
from config import Config
import json

logger = logging.getLogger(__name__)

class EventsSystem:
    def __init__(self):
        self.running = True
        self.active_events = {}
        
    def start_scheduler(self):
        """Start the event scheduler"""
        logger.info("Starting events system scheduler...")
        
        while self.running:
            try:
                with app.app_context():
                    self.check_and_create_events()
                    self.process_active_events()
                    self.cleanup_expired_events()
                
                # Check every 10 minutes
                time.sleep(600)
                
            except Exception as e:
                logger.error(f"Error in events scheduler: {e}")
                time.sleep(60)
    
    def check_and_create_events(self):
        """Check if new events should be created"""
        try:
            # Check if there are any active events
            active_events = GameEvent.query.filter(
                GameEvent.is_active == True,
                GameEvent.end_time > datetime.utcnow()
            ).count()
            
            # Create new event if no active events and random chance
            if active_events == 0 and random.random() < 0.3:  # 30% chance
                self.create_random_event()
            
            # Special events on certain times
            now = datetime.utcnow()
            
            # Weekend bonus event
            if now.weekday() >= 5 and active_events == 0:  # Saturday or Sunday
                if random.random() < 0.7:  # 70% chance on weekends
                    self.create_weekend_event()
            
            # Daily events at specific hours
            if now.hour in [12, 18, 21] and now.minute < 10:  # Peak hours
                if random.random() < 0.5:  # 50% chance
                    self.create_peak_hour_event()
        
        except Exception as e:
            logger.error(f"Error checking and creating events: {e}")
    
    def create_random_event(self):
        """Create a random event"""
        event_types = [
            'double_income',
            'energy_boost',
            'discount_business',
            'bonus_coins',
            'pvp_tournament',
            'market_crash',
            'golden_hour'
        ]
        
        event_type = random.choice(event_types)
        
        if event_type == 'double_income':
            self.create_double_income_event()
        elif event_type == 'energy_boost':
            self.create_energy_boost_event()
        elif event_type == 'discount_business':
            self.create_discount_event()
        elif event_type == 'bonus_coins':
            self.create_bonus_coins_event()
        elif event_type == 'pvp_tournament':
            self.create_pvp_tournament()
        elif event_type == 'market_crash':
            self.create_market_event()
        elif event_type == 'golden_hour':
            self.create_golden_hour_event()
    
    def create_double_income_event(self):
        """Create double income event"""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=random.randint(2, 6))
        
        event = GameEvent(
            event_type="double_income",
            title="🎉 Двойной доход!",
            description="Все бизнесы приносят двойной доход!",
            start_time=start_time,
            end_time=end_time,
            rewards=json.dumps({"income_multiplier": 2.0})
        )
        
        db.session.add(event)
        db.session.commit()
        
        logger.info(f"Created double income event until {end_time}")
    
    def create_energy_boost_event(self):
        """Create energy boost event"""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=4)
        
        event = GameEvent(
            event_type="energy_boost",
            title="⚡ Энергетический бонус!",
            description="Энергия восстанавливается в 3 раза быстрее!",
            start_time=start_time,
            end_time=end_time,
            rewards=json.dumps({"energy_multiplier": 3.0})
        )
        
        db.session.add(event)
        db.session.commit()
        
        logger.info(f"Created energy boost event until {end_time}")
    
    def create_discount_event(self):
        """Create business discount event"""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=8)
        
        discount = random.randint(20, 50)  # 20-50% discount
        
        event = GameEvent(
            event_type="discount_business",
            title=f"🏢 Скидка {discount}% на бизнесы!",
            description=f"Все бизнесы можно купить со скидкой {discount}%!",
            start_time=start_time,
            end_time=end_time,
            rewards=json.dumps({"discount_percentage": discount})
        )
        
        db.session.add(event)
        db.session.commit()
        
        logger.info(f"Created business discount event ({discount}%) until {end_time}")
    
    def create_bonus_coins_event(self):
        """Create bonus coins for all players event"""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=1)
        
        bonus_amount = random.randint(500, 2000)
        
        event = GameEvent(
            event_type="bonus_coins",
            title=f"💰 Бонус {bonus_amount} монет!",
            description=f"Все игроки получают {bonus_amount} бонусных монет!",
            start_time=start_time,
            end_time=end_time,
            rewards=json.dumps({"bonus_coins": bonus_amount})
        )
        
        db.session.add(event)
        db.session.commit()
        
        # Give bonus to all players immediately
        self.distribute_bonus_coins(bonus_amount)
        
        logger.info(f"Created bonus coins event ({bonus_amount}) until {end_time}")
    
    def create_weekend_event(self):
        """Create special weekend event"""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=12)
        
        event = GameEvent(
            event_type="weekend_special",
            title="🎪 Выходной бонус!",
            description="Удвоенный опыт и +50% к доходу от всех источников!",
            start_time=start_time,
            end_time=end_time,
            rewards=json.dumps({
                "experience_multiplier": 2.0,
                "income_multiplier": 1.5
            })
        )
        
        db.session.add(event)
        db.session.commit()
        
        logger.info(f"Created weekend special event until {end_time}")
    
    def create_pvp_tournament(self):
        """Create PvP tournament event"""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=24)
        
        event = GameEvent(
            event_type="pvp_tournament",
            title="⚔️ PvP Турнир!",
            description="Участвуйте в PvP битвах для получения призов! Победители получат особые награды.",
            start_time=start_time,
            end_time=end_time,
            rewards=json.dumps({
                "first_place": 10000,
                "second_place": 5000,
                "third_place": 2500,
                "participation": 500
            })
        )
        
        db.session.add(event)
        db.session.commit()
        
        logger.info(f"Created PvP tournament event until {end_time}")
    
    def create_market_event(self):
        """Create market fluctuation event"""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=6)
        
        # Random market condition
        if random.random() < 0.5:
            event_type = "market_boom"
            title = "📈 Экономический бум!"
            description = "Цены на сельхозпродукцию выросли на 50%!"
            price_multiplier = 1.5
        else:
            event_type = "market_crash"
            title = "📉 Экономический кризис!"
            description = "Цены на продукцию упали на 30%, но бизнесы стоят дешевле!"
            price_multiplier = 0.7
        
        event = GameEvent(
            event_type=event_type,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            rewards=json.dumps({"price_multiplier": price_multiplier})
        )
        
        db.session.add(event)
        db.session.commit()
        
        logger.info(f"Created market event ({event_type}) until {end_time}")
    
    def create_golden_hour_event(self):
        """Create golden hour event with multiple bonuses"""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=1)
        
        event = GameEvent(
            event_type="golden_hour",
            title="✨ Золотой час!",
            description="Тройной доход, двойной опыт, бесплатная энергия!",
            start_time=start_time,
            end_time=end_time,
            rewards=json.dumps({
                "income_multiplier": 3.0,
                "experience_multiplier": 2.0,
                "free_energy": True
            })
        )
        
        db.session.add(event)
        db.session.commit()
        
        logger.info(f"Created golden hour event until {end_time}")
    
    def create_peak_hour_event(self):
        """Create peak hour event"""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        
        event = GameEvent(
            event_type="peak_hour",
            title="🔥 Час пик!",
            description="Повышенная активность! +25% ко всем доходам.",
            start_time=start_time,
            end_time=end_time,
            rewards=json.dumps({"income_multiplier": 1.25})
        )
        
        db.session.add(event)
        db.session.commit()
        
        logger.info(f"Created peak hour event until {end_time}")
    
    def distribute_bonus_coins(self, amount):
        """Distribute bonus coins to all players"""
        try:
            players = Player.query.all()
            
            for player in players:
                player.coins += amount
                player.total_earned += amount
                
                # Add transaction record
                transaction = Transaction(
                    player_id=player.id,
                    transaction_type="income",
                    amount=amount,
                    description="Событийный бонус"
                )
                db.session.add(transaction)
            
            db.session.commit()
            logger.info(f"Distributed {amount} bonus coins to {len(players)} players")
            
        except Exception as e:
            logger.error(f"Error distributing bonus coins: {e}")
            db.session.rollback()
    
    def process_active_events(self):
        """Process effects of currently active events"""
        try:
            active_events = GameEvent.query.filter(
                GameEvent.is_active == True,
                GameEvent.start_time <= datetime.utcnow(),
                GameEvent.end_time > datetime.utcnow()
            ).all()
            
            # Update active events cache
            self.active_events = {}
            for event in active_events:
                self.active_events[event.event_type] = json.loads(event.rewards)
            
        except Exception as e:
            logger.error(f"Error processing active events: {e}")
    
    def cleanup_expired_events(self):
        """Mark expired events as inactive"""
        try:
            expired_count = GameEvent.query.filter(
                GameEvent.is_active == True,
                GameEvent.end_time <= datetime.utcnow()
            ).update({GameEvent.is_active: False})
            
            if expired_count > 0:
                db.session.commit()
                logger.info(f"Marked {expired_count} events as expired")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired events: {e}")
    
    def get_active_events(self):
        """Get list of currently active events"""
        try:
            with app.app_context():
                events = GameEvent.query.filter(
                    GameEvent.is_active == True,
                    GameEvent.start_time <= datetime.utcnow(),
                    GameEvent.end_time > datetime.utcnow()
                ).all()
                
                active_list = []
                for event in events:
                    time_left = event.end_time - datetime.utcnow()
                    hours_left = int(time_left.total_seconds() // 3600)
                    minutes_left = int((time_left.total_seconds() % 3600) // 60)
                    
                    active_list.append({
                        'id': event.id,
                        'title': event.title,
                        'description': event.description,
                        'type': event.event_type,
                        'time_left': f"{hours_left}ч {minutes_left}м"
                    })
                
                return active_list
                
        except Exception as e:
            logger.error(f"Error getting active events: {e}")
            return []
    
    def apply_event_modifiers(self, base_value, modifier_type):
        """Apply active event modifiers to values"""
        multiplier = 1.0
        
        for event_type, rewards in self.active_events.items():
            if modifier_type in rewards:
                event_multiplier = rewards[modifier_type]
                multiplier *= event_multiplier
        
        return int(base_value * multiplier)
    
    def has_active_modifier(self, modifier_type):
        """Check if a specific modifier is currently active"""
        for rewards in self.active_events.values():
            if modifier_type in rewards:
                return True
        return False
    
    def stop(self):
        """Stop the events system"""
        self.running = False
        logger.info("Events system stopped")
