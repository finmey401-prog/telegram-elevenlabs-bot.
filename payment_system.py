import logging
import os
from datetime import datetime, timedelta
from main import app, db
from models import Player, Transaction
from config import Config
import json

logger = logging.getLogger(__name__)

class PaymentSystem:
    def __init__(self):
        self.provider_token = Config.PAYMENT_PROVIDER_TOKEN
        self.payment_history = {}
        
    async def process_payment(self, pre_checkout_query, update, context):
        """Process payment after pre-checkout"""
        try:
            user_id = pre_checkout_query.from_user.id
            payload = pre_checkout_query.invoice_payload
            total_amount = pre_checkout_query.total_amount
            
            # Parse payload to determine what was purchased
            payment_data = json.loads(payload)
            
            with app.app_context():
                player = Player.query.filter_by(user_id=user_id).first()
                if not player:
                    logger.error(f"Player not found for payment: {user_id}")
                    return
                
                # Process different types of purchases
                if payment_data['type'] == 'vip':
                    await self.process_vip_purchase(player, payment_data, total_amount)
                elif payment_data['type'] == 'coins':
                    await self.process_coins_purchase(player, payment_data, total_amount)
                elif payment_data['type'] == 'premium_item':
                    await self.process_premium_item(player, payment_data, total_amount)
                
                # Record transaction
                transaction = Transaction(
                    player_id=player.id,
                    transaction_type="income",
                    amount=payment_data.get('coins_amount', 0),
                    description=f"Покупка: {payment_data['description']}"
                )
                db.session.add(transaction)
                
                db.session.commit()
                logger.info(f"Payment processed for player {player.username}: {payment_data['description']}")
                
        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            db.session.rollback()
    
    async def process_vip_purchase(self, player, payment_data, amount):
        """Process VIP subscription purchase"""
        vip_type = payment_data['vip_type']
        duration_days = payment_data.get('duration_days', 30)
        
        # Set VIP status
        player.vip_type = vip_type
        
        # If player already has VIP, extend it, otherwise start from now
        if player.vip_expires_at and player.vip_expires_at > datetime.utcnow():
            player.vip_expires_at += timedelta(days=duration_days)
        else:
            player.vip_expires_at = datetime.utcnow() + timedelta(days=duration_days)
        
        # Give VIP welcome bonus
        welcome_bonus = {
            'basic': 5000,
            'premium': 15000,
            'ultimate': 50000
        }
        
        bonus_coins = welcome_bonus.get(vip_type, 0)
        player.coins += bonus_coins
        player.total_earned += bonus_coins
        
        logger.info(f"VIP {vip_type} activated for player {player.username} until {player.vip_expires_at}")
    
    async def process_coins_purchase(self, player, payment_data, amount):
        """Process coins purchase"""
        coins_amount = payment_data['coins_amount']
        
        # Add coins to player account
        player.coins += coins_amount
        player.total_earned += coins_amount
        
        # Bonus coins for larger purchases
        if coins_amount >= 50000:
            bonus = int(coins_amount * 0.2)  # 20% bonus
            player.coins += bonus
            player.total_earned += bonus
        elif coins_amount >= 20000:
            bonus = int(coins_amount * 0.1)  # 10% bonus
            player.coins += bonus
            player.total_earned += bonus
        
        logger.info(f"Added {coins_amount} coins to player {player.username}")
    
    async def process_premium_item(self, player, payment_data, amount):
        """Process premium item purchase"""
        item_type = payment_data['item_type']
        
        # Process different premium items
        if item_type == 'energy_pack':
            player.energy = min(player.energy + 200, Config.MAX_ENERGY + 200)
        elif item_type == 'experience_boost':
            player.experience += 5000
        elif item_type == 'business_boost':
            # Give temporary business boost (would need separate tracking)
            pass
        
        logger.info(f"Premium item {item_type} given to player {player.username}")
    
    def create_vip_invoice(self, vip_type, duration_days=30):
        """Create invoice for VIP purchase"""
        price = Config.VIP_PRICES.get(vip_type, 299)
        
        # Adjust price for duration
        if duration_days == 7:
            price = int(price * 0.3)  # Weekly price
        elif duration_days == 90:
            price = int(price * 2.5)  # Quarterly price
        
        title = f"VIP {vip_type.capitalize()} подписка"
        description = f"VIP {vip_type} статус на {duration_days} дней"
        
        payload = json.dumps({
            'type': 'vip',
            'vip_type': vip_type,
            'duration_days': duration_days,
            'description': title
        })
        
        return {
            'title': title,
            'description': description,
            'payload': payload,
            'provider_token': self.provider_token,
            'currency': 'RUB',
            'prices': [{'label': title, 'amount': price * 100}]  # Amount in kopecks
        }
    
    def create_coins_invoice(self, coins_amount):
        """Create invoice for coins purchase"""
        # Pricing: 1000 coins = 99 rubles
        price = int(coins_amount * 0.099)
        
        title = f"{coins_amount:,} монет"
        description = f"Пакет из {coins_amount:,} внутриигровых монет"
        
        payload = json.dumps({
            'type': 'coins',
            'coins_amount': coins_amount,
            'description': title
        })
        
        return {
            'title': title,
            'description': description,
            'payload': payload,
            'provider_token': self.provider_token,
            'currency': 'RUB',
            'prices': [{'label': title, 'amount': price * 100}]
        }
    
    def create_premium_item_invoice(self, item_type):
        """Create invoice for premium item"""
        items = {
            'energy_pack': {
                'title': 'Пакет энергии',
                'description': '+200 энергии',
                'price': 199
            },
            'experience_boost': {
                'title': 'Бустер опыта',
                'description': '+5000 опыта',
                'price': 299
            },
            'business_boost': {
                'title': 'Бизнес бустер',
                'description': 'Ускорение бизнеса на 24 часа',
                'price': 399
            }
        }
        
        item = items.get(item_type)
        if not item:
            return None
        
        payload = json.dumps({
            'type': 'premium_item',
            'item_type': item_type,
            'description': item['title']
        })
        
        return {
            'title': item['title'],
            'description': item['description'],
            'payload': payload,
            'provider_token': self.provider_token,
            'currency': 'RUB',
            'prices': [{'label': item['title'], 'amount': item['price'] * 100}]
        }
    
    def get_popular_packages(self):
        """Get list of popular purchase packages"""
        packages = []
        
        # VIP packages
        for vip_type, price in Config.VIP_PRICES.items():
            benefits = Config.VIP_BENEFITS.get(vip_type, {})
            packages.append({
                'type': 'vip',
                'name': f'VIP {vip_type.capitalize()}',
                'price': price,
                'description': f"Бонус энергии: +{benefits.get('energy_bonus', 0)}, "
                              f"Множитель дохода: x{benefits.get('income_multiplier', 1)}",
                'popular': vip_type == 'premium'
            })
        
        # Coin packages
        coin_packages = [
            (5000, 299, False),
            (15000, 799, True),  # Most popular
            (50000, 2499, False),
            (150000, 6999, False)
        ]
        
        for coins, price, popular in coin_packages:
            packages.append({
                'type': 'coins',
                'name': f'{coins:,} монет',
                'price': price,
                'description': f'{coins:,} внутриигровых монет',
                'popular': popular
            })
        
        # Premium items
        premium_items = [
            ('energy_pack', 'Пакет энергии', 199, '+200 энергии'),
            ('experience_boost', 'Бустер опыта', 299, '+5000 опыта'),
            ('business_boost', 'Бизнес бустер', 399, 'Ускорение на 24ч')
        ]
        
        for item_type, name, price, desc in premium_items:
            packages.append({
                'type': 'premium_item',
                'name': name,
                'price': price,
                'description': desc,
                'popular': False
            })
        
        return packages
    
    def get_player_purchase_history(self, player_id, limit=20):
        """Get purchase history for player"""
        try:
            with app.app_context():
                transactions = Transaction.query.filter(
                    Transaction.player_id == player_id,
                    Transaction.description.like('Покупка:%')
                ).order_by(Transaction.created_at.desc()).limit(limit).all()
                
                history = []
                for trans in transactions:
                    history.append({
                        'id': trans.id,
                        'description': trans.description,
                        'amount': trans.amount,
                        'date': trans.created_at.strftime('%d.%m.%Y %H:%M')
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Error getting purchase history: {e}")
            return []
    
    def calculate_player_ltv(self, player_id):
        """Calculate player lifetime value"""
        try:
            with app.app_context():
                purchase_transactions = Transaction.query.filter(
                    Transaction.player_id == player_id,
                    Transaction.description.like('Покупка:%')
                ).all()
                
                # This would need to track actual money spent, not in-game coins
                # For now, estimate based on purchase frequency and amounts
                total_purchases = len(purchase_transactions)
                
                if total_purchases == 0:
                    return 0
                
                # Rough estimation based on purchase patterns
                estimated_ltv = total_purchases * 500  # 500 rubles per purchase average
                
                return estimated_ltv
                
        except Exception as e:
            logger.error(f"Error calculating LTV: {e}")
            return 0
