from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from main import db
import json

class Player(db.Model):
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)  # Telegram user ID
    username = Column(String(100))
    coins = Column(Integer, default=1000)
    energy = Column(Integer, default=100)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    last_energy_update = Column(DateTime, default=datetime.utcnow)
    last_daily_bonus = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # VIP status
    vip_type = Column(String(20))  # basic, premium, ultimate
    vip_expires_at = Column(DateTime)
    
    # Statistics
    total_earned = Column(Integer, default=0)
    total_spent = Column(Integer, default=0)
    pvp_wins = Column(Integer, default=0)
    pvp_losses = Column(Integer, default=0)
    
    # Relationships
    businesses = relationship("Business", back_populates="owner")
    farms = relationship("Farm", back_populates="owner")
    transactions = relationship("Transaction", back_populates="player")
    
    def __repr__(self):
        return f'<Player {self.username}>'
    
    @property
    def is_vip(self):
        return self.vip_type and self.vip_expires_at and self.vip_expires_at > datetime.utcnow()
    
    def update_energy(self):
        """Update player energy based on time passed"""
        from config import Config
        
        now = datetime.utcnow()
        time_diff = (now - self.last_energy_update).total_seconds()
        energy_to_add = int(time_diff / 60) * Config.ENERGY_REGEN_RATE
        
        if energy_to_add > 0:
            max_energy = Config.MAX_ENERGY
            if self.is_vip and self.vip_type in Config.VIP_BENEFITS:
                max_energy += Config.VIP_BENEFITS[self.vip_type]['energy_bonus']
            
            self.energy = min(self.energy + energy_to_add, max_energy)
            self.last_energy_update = now
    
    def can_claim_daily_bonus(self):
        """Check if player can claim daily bonus"""
        if not self.last_daily_bonus:
            return True
        
        time_diff = datetime.utcnow() - self.last_daily_bonus
        return time_diff.total_seconds() >= 86400  # 24 hours

class Business(db.Model):
    __tablename__ = 'businesses'
    
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    business_type = Column(String(50), nullable=False)
    level = Column(Integer, default=1)
    last_collection = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("Player", back_populates="businesses")
    
    def __repr__(self):
        return f'<Business {self.business_type} Level {self.level}>'
    
    def calculate_income(self):
        """Calculate available income for collection"""
        from config import Config
        
        business_config = Config.BUSINESS_TYPES.get(self.business_type)
        if not business_config:
            return 0
        
        base_income = business_config['income'] * self.level
        collection_time = business_config['time']
        
        time_passed = (datetime.utcnow() - self.last_collection).total_seconds()
        collections_ready = int(time_passed / collection_time)
        
        # Apply VIP multiplier if owner is VIP
        multiplier = 1.0
        if self.owner.is_vip and self.owner.vip_type in Config.VIP_BENEFITS:
            multiplier = Config.VIP_BENEFITS[self.owner.vip_type]['income_multiplier']
        
        return int(base_income * collections_ready * multiplier)

class Farm(db.Model):
    __tablename__ = 'farms'
    
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    crop_type = Column(String(50))
    planted_at = Column(DateTime)
    slots = Column(Integer, default=4)
    level = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("Player", back_populates="farms")
    
    def __repr__(self):
        return f'<Farm Level {self.level}>'
    
    def is_ready_to_harvest(self):
        """Check if crop is ready for harvest"""
        if not self.crop_type or not self.planted_at:
            return False
        
        from config import Config
        crop_config = Config.CROPS.get(self.crop_type)
        if not crop_config:
            return False
        
        grow_time = crop_config['grow_time']
        if self.owner.is_vip and self.owner.vip_type in Config.VIP_BENEFITS:
            speed_boost = Config.VIP_BENEFITS[self.owner.vip_type]['speed_boost']
            grow_time = int(grow_time / speed_boost)
        
        time_passed = (datetime.utcnow() - self.planted_at).total_seconds()
        return time_passed >= grow_time

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    transaction_type = Column(String(50), nullable=False)  # income, expense, pvp_win, pvp_loss
    amount = Column(Integer, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    player = relationship("Player", back_populates="transactions")
    
    def __repr__(self):
        return f'<Transaction {self.transaction_type}: {self.amount}>'

class PvPBattle(db.Model):
    __tablename__ = 'pvp_battles'
    
    id = Column(Integer, primary_key=True)
    attacker_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    defender_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    winner_id = Column(Integer, ForeignKey('players.id'))
    amount_stolen = Column(Integer, default=0)
    battle_log = Column(Text)  # JSON string with battle details
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    attacker = relationship("Player", foreign_keys=[attacker_id])
    defender = relationship("Player", foreign_keys=[defender_id])
    winner = relationship("Player", foreign_keys=[winner_id])
    
    def __repr__(self):
        return f'<PvPBattle {self.attacker_id} vs {self.defender_id}>'

class GameEvent(db.Model):
    __tablename__ = 'game_events'
    
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    rewards = Column(Text)  # JSON string with reward details
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<GameEvent {self.title}>'
    
    @property
    def is_running(self):
        now = datetime.utcnow()
        return self.is_active and self.start_time <= now <= self.end_time

class PlayerActivity(db.Model):
    __tablename__ = 'player_activities'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    action_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text)  # JSON string with action details
    
    # Relationships
    player = relationship("Player")
    
    def __repr__(self):
        return f'<PlayerActivity {self.action_type} by {self.player_id}>'

class Leaderboard(db.Model):
    __tablename__ = 'leaderboard'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    category = Column(String(50), nullable=False)  # coins, level, pvp_wins
    score = Column(Integer, nullable=False)
    rank = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    player = relationship("Player")
    
    def __repr__(self):
        return f'<Leaderboard {self.category}: Rank {self.rank}>'
