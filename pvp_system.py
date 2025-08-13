import logging
import random
from datetime import datetime, timedelta
from main import app, db
from models import Player, PvPBattle, Transaction
from config import Config
import json

logger = logging.getLogger(__name__)

class PvPSystem:
    def __init__(self):
        self.battle_cooldowns = {}  # Track battle cooldowns per player
        
    def can_attack(self, attacker_id, defender_id):
        """Check if attacker can attack defender"""
        try:
            with app.app_context():
                attacker = Player.query.get(attacker_id)
                defender = Player.query.get(defender_id)
                
                if not attacker or not defender:
                    return False, "Игрок не найден"
                
                if attacker_id == defender_id:
                    return False, "Нельзя атаковать самого себя"
                
                if attacker.coins < Config.ATTACK_COST:
                    return False, f"Недостаточно монет для атаки ({Config.ATTACK_COST})"
                
                if attacker.energy < 30:
                    return False, "Недостаточно энергии для атаки (30)"
                
                # Check cooldown
                cooldown_key = f"{attacker_id}_{defender_id}"
                if cooldown_key in self.battle_cooldowns:
                    cooldown_end = self.battle_cooldowns[cooldown_key]
                    if datetime.utcnow() < cooldown_end:
                        remaining = (cooldown_end - datetime.utcnow()).seconds
                        return False, f"Атака будет доступна через {remaining} секунд"
                
                # Check level difference (can't attack players more than 5 levels below)
                if attacker.level > defender.level + 5:
                    return False, "Нельзя атаковать игроков намного слабее вас"
                
                # Check if defender has enough coins to steal
                if defender.coins < 100:
                    return False, "У защитника слишком мало монет для атаки"
                
                return True, "Атака возможна"
                
        except Exception as e:
            logger.error(f"Error checking attack possibility: {e}")
            return False, "Ошибка проверки возможности атаки"
    
    def execute_battle(self, attacker_id, defender_id):
        """Execute PvP battle between two players"""
        try:
            with app.app_context():
                can_attack, message = self.can_attack(attacker_id, defender_id)
                if not can_attack:
                    return False, None, message
                
                attacker = Player.query.get(attacker_id)
                defender = Player.query.get(defender_id)
                
                # Calculate battle outcome
                battle_result = self.calculate_battle_outcome(attacker, defender)
                
                # Process battle costs
                attacker.coins -= Config.ATTACK_COST
                attacker.energy -= 30
                
                winner_id = attacker_id if battle_result['attacker_wins'] else defender_id
                loser_id = defender_id if battle_result['attacker_wins'] else attacker_id
                
                # Update player stats
                if battle_result['attacker_wins']:
                    attacker.pvp_wins += 1
                    defender.pvp_losses += 1
                    
                    # Steal coins
                    stolen_amount = battle_result['stolen_amount']
                    attacker.coins += stolen_amount
                    defender.coins -= stolen_amount
                    
                    # Add experience for winner
                    attacker.experience += 100
                    
                else:
                    attacker.pvp_losses += 1
                    defender.pvp_wins += 1
                    
                    # Defender gets experience for successful defense
                    defender.experience += 50
                    
                    stolen_amount = 0
                
                # Create battle record
                battle = PvPBattle(
                    attacker_id=attacker_id,
                    defender_id=defender_id,
                    winner_id=winner_id,
                    amount_stolen=stolen_amount,
                    battle_log=json.dumps(battle_result['battle_log'])
                )
                db.session.add(battle)
                
                # Add transaction records
                attack_transaction = Transaction(
                    player_id=attacker_id,
                    transaction_type="expense",
                    amount=Config.ATTACK_COST,
                    description=f"PvP атака на {defender.username}"
                )
                db.session.add(attack_transaction)
                
                if stolen_amount > 0:
                    steal_transaction = Transaction(
                        player_id=attacker_id,
                        transaction_type="pvp_win",
                        amount=stolen_amount,
                        description=f"Украдено у {defender.username}"
                    )
                    db.session.add(steal_transaction)
                    
                    loss_transaction = Transaction(
                        player_id=defender_id,
                        transaction_type="pvp_loss",
                        amount=stolen_amount,
                        description=f"Украдено игроком {attacker.username}"
                    )
                    db.session.add(loss_transaction)
                
                # Set battle cooldown (1 hour)
                cooldown_key = f"{attacker_id}_{defender_id}"
                self.battle_cooldowns[cooldown_key] = datetime.utcnow() + timedelta(hours=1)
                
                db.session.commit()
                
                return True, battle, "Битва завершена"
                
        except Exception as e:
            logger.error(f"Error executing battle: {e}")
            db.session.rollback()
            return False, None, "Ошибка выполнения битвы"
    
    def calculate_battle_outcome(self, attacker, defender):
        """Calculate the outcome of a PvP battle"""
        # Calculate base power for each player
        attacker_power = self.calculate_player_power(attacker)
        defender_power = self.calculate_player_power(defender)
        
        # Add randomness factor (±20%)
        attacker_final = attacker_power * random.uniform(0.8, 1.2)
        defender_final = defender_power * random.uniform(0.8, 1.2)
        
        # Determine winner
        attacker_wins = attacker_final > defender_final
        
        # Calculate stolen amount
        stolen_amount = 0
        if attacker_wins:
            steal_percentage = random.randint(Config.MIN_STEAL_PERCENTAGE, Config.MAX_STEAL_PERCENTAGE)
            stolen_amount = min(
                int(defender.coins * steal_percentage / 100),
                defender.coins  # Can't steal more than defender has
            )
        
        # Create battle log
        battle_log = {
            'attacker_power': round(attacker_final, 2),
            'defender_power': round(defender_final, 2),
            'attacker_wins': attacker_wins,
            'stolen_amount': stolen_amount,
            'battle_events': self.generate_battle_events(attacker, defender, attacker_wins)
        }
        
        return {
            'attacker_wins': attacker_wins,
            'stolen_amount': stolen_amount,
            'battle_log': battle_log
        }
    
    def calculate_player_power(self, player):
        """Calculate player's battle power"""
        # Base power from level
        base_power = player.level * 10
        
        # Power from businesses (each business adds power)
        business_power = len(player.businesses) * 5
        
        # Power from farm level
        farm_power = 0
        if player.farms:
            farm_power = sum(farm.level * 3 for farm in player.farms)
        
        # Power from wealth (logarithmic scaling)
        wealth_power = 0
        if player.coins > 1000:
            import math
            wealth_power = math.log10(player.coins / 1000) * 5
        
        # VIP bonus
        vip_bonus = 0
        if player.is_vip:
            vip_multipliers = {'basic': 1.1, 'premium': 1.2, 'ultimate': 1.3}
            vip_bonus = vip_multipliers.get(player.vip_type, 1.0)
        
        total_power = (base_power + business_power + farm_power + wealth_power)
        
        if vip_bonus > 0:
            total_power *= vip_bonus
        
        return total_power
    
    def generate_battle_events(self, attacker, defender, attacker_wins):
        """Generate narrative battle events"""
        events = []
        
        # Opening move
        events.append(f"{attacker.username} начинает атаку на {defender.username}!")
        
        # Random battle events
        battle_actions = [
            f"{attacker.username} использует мощную атаку!",
            f"{defender.username} защищается!",
            f"{attacker.username} наносит критический удар!",
            f"{defender.username} контратакует!",
            "Напряженная схватка продолжается...",
            "Бойцы обмениваются ударами!"
        ]
        
        # Add 2-3 random events
        for _ in range(random.randint(2, 3)):
            events.append(random.choice(battle_actions))
        
        # Final outcome
        if attacker_wins:
            events.append(f"🎉 {attacker.username} побеждает!")
            if attacker_wins:
                events.append(f"💰 Украдено {attacker_wins} монет!")
        else:
            events.append(f"🛡️ {defender.username} успешно защищается!")
        
        return events
    
    def get_pvp_targets(self, player_id, limit=10):
        """Get suitable PvP targets for player"""
        try:
            with app.app_context():
                player = Player.query.get(player_id)
                if not player:
                    return []
                
                # Find players within reasonable level range and with enough coins
                min_level = max(1, player.level - 3)
                max_level = player.level + 5
                
                targets = Player.query.filter(
                    Player.id != player_id,
                    Player.level >= min_level,
                    Player.level <= max_level,
                    Player.coins >= 1000  # Must have at least 1000 coins
                ).order_by(Player.coins.desc()).limit(limit).all()
                
                # Filter out players on cooldown
                available_targets = []
                for target in targets:
                    cooldown_key = f"{player_id}_{target.id}"
                    if cooldown_key not in self.battle_cooldowns or \
                       datetime.utcnow() >= self.battle_cooldowns[cooldown_key]:
                        available_targets.append({
                            'id': target.id,
                            'username': target.username,
                            'level': target.level,
                            'coins': target.coins,
                            'power': round(self.calculate_player_power(target), 1)
                        })
                
                return available_targets
                
        except Exception as e:
            logger.error(f"Error getting PvP targets: {e}")
            return []
    
    def get_battle_history(self, player_id, limit=20):
        """Get recent battle history for player"""
        try:
            with app.app_context():
                battles = PvPBattle.query.filter(
                    (PvPBattle.attacker_id == player_id) | (PvPBattle.defender_id == player_id)
                ).order_by(PvPBattle.created_at.desc()).limit(limit).all()
                
                history = []
                for battle in battles:
                    is_attacker = battle.attacker_id == player_id
                    won = battle.winner_id == player_id
                    
                    opponent = battle.defender if is_attacker else battle.attacker
                    
                    history.append({
                        'id': battle.id,
                        'opponent': opponent.username,
                        'role': 'Атакующий' if is_attacker else 'Защищающийся',
                        'result': 'Победа' if won else 'Поражение',
                        'amount': battle.amount_stolen if won else -battle.amount_stolen,
                        'date': battle.created_at.strftime('%d.%m.%Y %H:%M')
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Error getting battle history: {e}")
            return []
    
    def get_pvp_rankings(self, limit=50):
        """Get PvP rankings by wins"""
        try:
            with app.app_context():
                top_players = Player.query.filter(
                    Player.pvp_wins > 0
                ).order_by(Player.pvp_wins.desc()).limit(limit).all()
                
                rankings = []
                for rank, player in enumerate(top_players, 1):
                    win_rate = 0
                    total_battles = player.pvp_wins + player.pvp_losses
                    if total_battles > 0:
                        win_rate = round(player.pvp_wins / total_battles * 100, 1)
                    
                    rankings.append({
                        'rank': rank,
                        'username': player.username,
                        'level': player.level,
                        'wins': player.pvp_wins,
                        'losses': player.pvp_losses,
                        'win_rate': win_rate,
                        'power': round(self.calculate_player_power(player), 1)
                    })
                
                return rankings
                
        except Exception as e:
            logger.error(f"Error getting PvP rankings: {e}")
            return []
