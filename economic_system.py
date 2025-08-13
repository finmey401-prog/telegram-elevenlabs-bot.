import logging
from datetime import datetime, timedelta
from main import app, db
from models import Player, Transaction
from config import Config
import random

logger = logging.getLogger(__name__)

class EconomicSystem:
    def __init__(self):
        self.market_fluctuation = {}  # Track market price fluctuations
        self.inflation_rate = 0.02  # 2% inflation per month
        
    def process_transaction(self, player_id, amount, transaction_type, description):
        """Process a financial transaction"""
        try:
            with app.app_context():
                player = Player.query.get(player_id)
                if not player:
                    return False, "Игрок не найден"
                
                if transaction_type == "expense" and player.coins < amount:
                    return False, "Недостаточно монет"
                
                # Process transaction
                if transaction_type == "income":
                    player.coins += amount
                    player.total_earned += amount
                elif transaction_type == "expense":
                    player.coins -= amount
                    player.total_spent += amount
                
                # Add transaction record
                transaction = Transaction(
                    player_id=player_id,
                    transaction_type=transaction_type,
                    amount=amount,
                    description=description
                )
                
                db.session.add(transaction)
                db.session.commit()
                
                return True, "Транзакция выполнена успешно"
                
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            db.session.rollback()
            return False, "Ошибка обработки транзакции"
    
    def calculate_market_prices(self):
        """Calculate current market prices with fluctuation"""
        prices = {}
        
        # Base prices from config
        for crop, config in Config.CROPS.items():
            base_price = config['sell_price']
            
            # Add market fluctuation (-20% to +30%)
            fluctuation = random.uniform(-0.2, 0.3)
            current_price = int(base_price * (1 + fluctuation))
            
            prices[crop] = {
                'buy_price': config['cost'],
                'sell_price': current_price,
                'fluctuation': fluctuation
            }
        
        return prices
    
    def calculate_business_roi(self, business_type):
        """Calculate Return on Investment for business"""
        config = Config.BUSINESS_TYPES.get(business_type)
        if not config:
            return 0
        
        cost = config['cost']
        income_per_hour = config['income'] * (3600 / config['time'])
        
        # ROI = (income_per_hour * 24 * 30) / cost * 100 (monthly ROI percentage)
        monthly_roi = (income_per_hour * 24 * 30) / cost * 100
        return round(monthly_roi, 2)
    
    def get_investment_recommendations(self, player):
        """Get personalized investment recommendations"""
        recommendations = []
        
        # Recommend based on player's current wealth
        if player.coins >= 200000:
            recommendations.append({
                'type': 'business',
                'item': 'bank',
                'reason': 'Высокий доход для вашего капитала',
                'roi': self.calculate_business_roi('bank')
            })
        elif player.coins >= 50000:
            recommendations.append({
                'type': 'business',
                'item': 'factory',
                'reason': 'Оптимальное соотношение цена/доход',
                'roi': self.calculate_business_roi('factory')
            })
        elif player.coins >= 15000:
            recommendations.append({
                'type': 'business',
                'item': 'shop',
                'reason': 'Стабильный доход для среднего капитала',
                'roi': self.calculate_business_roi('shop')
            })
        else:
            recommendations.append({
                'type': 'business',
                'item': 'cafe',
                'reason': 'Лучший стартовый бизнес',
                'roi': self.calculate_business_roi('cafe')
            })
        
        # Always recommend farm improvements if affordable
        from models import Farm
        farm = Farm.query.filter_by(owner_id=player.id).first()
        if farm and player.coins >= 5000:
            recommendations.append({
                'type': 'upgrade',
                'item': 'farm',
                'reason': 'Увеличит количество слотов для посева',
                'cost': 5000 * farm.level
            })
        
        return recommendations
    
    def calculate_wealth_distribution(self):
        """Calculate wealth distribution among players"""
        try:
            with app.app_context():
                players = Player.query.all()
                
                if not players:
                    return {}
                
                total_wealth = sum(p.coins for p in players)
                
                # Sort players by wealth
                wealthy_players = sorted(players, key=lambda p: p.coins, reverse=True)
                
                # Calculate percentiles
                top_1_percent = wealthy_players[:max(1, len(players) // 100)]
                top_10_percent = wealthy_players[:max(1, len(players) // 10)]
                
                top_1_wealth = sum(p.coins for p in top_1_percent)
                top_10_wealth = sum(p.coins for p in top_10_percent)
                
                distribution = {
                    'total_players': len(players),
                    'total_wealth': total_wealth,
                    'average_wealth': total_wealth // len(players) if players else 0,
                    'top_1_percent_wealth': top_1_wealth,
                    'top_10_percent_wealth': top_10_wealth,
                    'wealth_inequality': round(top_10_wealth / total_wealth * 100, 2) if total_wealth > 0 else 0
                }
                
                return distribution
                
        except Exception as e:
            logger.error(f"Error calculating wealth distribution: {e}")
            return {}
    
    def detect_economic_anomalies(self):
        """Detect unusual economic patterns (anti-cheat)"""
        anomalies = []
        
        try:
            with app.app_context():
                # Look for players with suspicious transaction patterns
                players = Player.query.all()
                
                for player in players:
                    # Check for unrealistic wealth accumulation
                    account_age_hours = (datetime.utcnow() - player.created_at).total_seconds() / 3600
                    
                    if account_age_hours > 0:
                        wealth_per_hour = player.coins / account_age_hours
                        
                        # Flag if earning more than 10,000 coins per hour consistently
                        if wealth_per_hour > 10000 and player.coins > 50000:
                            anomalies.append({
                                'player_id': player.id,
                                'type': 'suspicious_wealth',
                                'details': f"Earning {wealth_per_hour:.0f} coins/hour"
                            })
                    
                    # Check for unusual transaction patterns
                    recent_transactions = Transaction.query.filter(
                        Transaction.player_id == player.id,
                        Transaction.created_at >= datetime.utcnow() - timedelta(hours=24)
                    ).all()
                    
                    if len(recent_transactions) > 1000:  # More than 1000 transactions per day
                        anomalies.append({
                            'player_id': player.id,
                            'type': 'excessive_transactions',
                            'details': f"{len(recent_transactions)} transactions in 24h"
                        })
                
                return anomalies
                
        except Exception as e:
            logger.error(f"Error detecting economic anomalies: {e}")
            return []
    
    def calculate_daily_economy_stats(self):
        """Calculate daily economic statistics"""
        try:
            with app.app_context():
                today = datetime.utcnow().date()
                today_start = datetime.combine(today, datetime.min.time())
                
                # Total transactions today
                today_transactions = Transaction.query.filter(
                    Transaction.created_at >= today_start
                ).all()
                
                total_income = sum(t.amount for t in today_transactions if t.transaction_type == 'income')
                total_expenses = sum(t.amount for t in today_transactions if t.transaction_type == 'expense')
                
                # Active players today (players with transactions)
                active_players = len(set(t.player_id for t in today_transactions))
                
                # New players today
                new_players = Player.query.filter(
                    Player.created_at >= today_start
                ).count()
                
                stats = {
                    'date': today.isoformat(),
                    'total_transactions': len(today_transactions),
                    'total_income': total_income,
                    'total_expenses': total_expenses,
                    'net_economy_flow': total_income - total_expenses,
                    'active_players': active_players,
                    'new_players': new_players
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"Error calculating daily economy stats: {e}")
            return {}
    
    def adjust_game_balance(self):
        """Automatically adjust game balance based on economic data"""
        try:
            stats = self.calculate_daily_economy_stats()
            distribution = self.calculate_wealth_distribution()
            
            adjustments = []
            
            # If wealth inequality is too high (>80%), increase income for new players
            if distribution.get('wealth_inequality', 0) > 80:
                adjustments.append({
                    'type': 'increase_starting_coins',
                    'reason': 'High wealth inequality detected',
                    'current_value': Config.STARTING_COINS,
                    'suggested_value': int(Config.STARTING_COINS * 1.2)
                })
            
            # If net economy flow is too negative, reduce business costs
            net_flow = stats.get('net_economy_flow', 0)
            if net_flow < -100000:  # More than 100k coins removed from economy daily
                adjustments.append({
                    'type': 'reduce_business_costs',
                    'reason': 'Deflation detected in economy',
                    'adjustment_factor': 0.9
                })
            
            return adjustments
            
        except Exception as e:
            logger.error(f"Error adjusting game balance: {e}")
            return []
