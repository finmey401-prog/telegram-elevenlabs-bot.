import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, PreCheckoutQueryHandler
from telegram.constants import ParseMode
import asyncio
from datetime import datetime, timedelta
import json

from main import app, db
from models import Player, Business, Farm, Transaction, PvPBattle, GameEvent
from game_engine import GameEngine
from economic_system import EconomicSystem
from pvp_system import PvPSystem
from events_system import EventsSystem
from payment_system import PaymentSystem
from localization import Localization
from security import SecurityManager
from config import Config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.application = None
        self.game_engine = GameEngine()
        self.economic_system = EconomicSystem()
        self.pvp_system = PvPSystem()
        self.events_system = EventsSystem()
        self.payment_system = PaymentSystem()
        self.localization = Localization()
        self.security = SecurityManager()
        
    def start(self):
        """Start the Telegram bot"""
        with app.app_context():
            # Create application
            self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
            
            # Add handlers
            self.add_handlers()
            
            # Run the bot
            logger.info("Bot is starting...")
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    def add_handlers(self):
        """Add all command and callback handlers"""
        app = self.application
        
        # Command handlers
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("profile", self.profile_command))
        app.add_handler(CommandHandler("business", self.business_command))
        app.add_handler(CommandHandler("farm", self.farm_command))
        app.add_handler(CommandHandler("pvp", self.pvp_command))
        app.add_handler(CommandHandler("leaderboard", self.leaderboard_command))
        app.add_handler(CommandHandler("events", self.events_command))
        app.add_handler(CommandHandler("vip", self.vip_command))
        app.add_handler(CommandHandler("daily", self.daily_bonus_command))
        
        # Callback query handlers
        app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Payment handlers
        app.add_handler(PreCheckoutQueryHandler(self.precheckout_callback))
        
        # Message handler for unknown commands
        app.add_handler(MessageHandler(filters.COMMAND, self.unknown_command))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Security check
        if not self.security.check_rate_limit(user.id):
            await update.message.reply_text(
                self.localization.get_text('rate_limit_exceeded')
            )
            return
        
        with app.app_context():
            # Get or create player
            player = Player.query.filter_by(user_id=user.id).first()
            
            if not player:
                # Create new player
                player = Player(
                    user_id=user.id,
                    username=user.username or f"Игрок_{user.id}",
                    coins=Config.STARTING_COINS,
                    energy=Config.STARTING_ENERGY
                )
                db.session.add(player)
                db.session.commit()
                
                # Create initial farm
                farm = Farm(owner_id=player.id)
                db.session.add(farm)
                db.session.commit()
                
                welcome_text = self.localization.get_text('welcome_new_player', 
                    username=player.username, coins=Config.STARTING_COINS)
            else:
                welcome_text = self.localization.get_text('welcome_back', 
                    username=player.username)
        
        keyboard = [
            [InlineKeyboardButton("📊 Профиль", callback_data="profile")],
            [
                InlineKeyboardButton("🏢 Бизнес", callback_data="business"),
                InlineKeyboardButton("🚜 Ферма", callback_data="farm")
            ],
            [
                InlineKeyboardButton("⚔️ PvP", callback_data="pvp"),
                InlineKeyboardButton("🏆 Рейтинг", callback_data="leaderboard")
            ],
            [
                InlineKeyboardButton("🎁 Ежедневный бонус", callback_data="daily_bonus"),
                InlineKeyboardButton("🎪 События", callback_data="events")
            ],
            [InlineKeyboardButton("💎 VIP", callback_data="vip")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /profile command"""
        user = update.effective_user
        
        with app.app_context():
            player = Player.query.filter_by(user_id=user.id).first()
            
            if not player:
                await update.message.reply_text(
                    self.localization.get_text('not_registered')
                )
                return
            
            # Update energy
            player.update_energy()
            db.session.commit()
            
            # Calculate statistics
            total_businesses = len(player.businesses)
            total_farms = len(player.farms)
            
            profile_text = self.localization.get_text('profile_info',
                username=player.username,
                level=player.level,
                coins=player.coins,
                energy=player.energy,
                total_businesses=total_businesses,
                total_farms=total_farms,
                pvp_wins=player.pvp_wins,
                pvp_losses=player.pvp_losses,
                vip_status=player.vip_type if player.is_vip else "Нет"
            )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="profile")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(profile_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def business_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /business command"""
        await self.show_business_menu(update, context)
    
    async def show_business_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show business management menu"""
        user = update.effective_user
        
        with app.app_context():
            player = Player.query.filter_by(user_id=user.id).first()
            
            if not player:
                await update.message.reply_text(
                    self.localization.get_text('not_registered')
                )
                return
            
            businesses = Business.query.filter_by(owner_id=player.id).all()
            
            business_text = "<b>🏢 Управление бизнесом</b>\n\n"
            
            if businesses:
                for business in businesses:
                    income = business.calculate_income()
                    business_text += f"• {business.business_type.capitalize()} (Уровень {business.level})\n"
                    business_text += f"  💰 Доступно: {income} монет\n\n"
            else:
                business_text += "У вас пока нет бизнесов.\n"
            
            business_text += "\n<b>Доступные бизнесы:</b>\n"
            for btype, config in Config.BUSINESS_TYPES.items():
                business_text += f"• {btype.capitalize()}: {config['cost']} монет\n"
        
        keyboard = []
        
        # Add collect buttons for existing businesses
        if businesses:
            for business in businesses:
                income = business.calculate_income()
                if income > 0:
                    keyboard.append([InlineKeyboardButton(
                        f"💰 Собрать {business.business_type} ({income})",
                        callback_data=f"collect_business_{business.id}"
                    )])
        
        # Add buy business buttons
        buy_row = []
        for btype in Config.BUSINESS_TYPES.keys():
            buy_row.append(InlineKeyboardButton(
                f"🏢 {btype.capitalize()}", 
                callback_data=f"buy_business_{btype}"
            ))
            if len(buy_row) == 2:
                keyboard.append(buy_row)
                buy_row = []
        
        if buy_row:
            keyboard.append(buy_row)
        
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                business_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                business_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user = query.from_user
        
        # Security check
        if not self.security.check_rate_limit(user.id):
            await query.edit_message_text(
                self.localization.get_text('rate_limit_exceeded')
            )
            return
        
        with app.app_context():
            # Log player activity
            self.security.log_player_activity(user.id, data)
            
            if data == "main_menu":
                await self.show_main_menu(update, context)
            elif data == "profile":
                await self.show_profile(update, context)
            elif data == "business":
                await self.show_business_menu(update, context)
            elif data == "farm":
                await self.show_farm_menu(update, context)
            elif data == "pvp":
                await self.show_pvp_menu(update, context)
            elif data == "leaderboard":
                await self.show_leaderboard(update, context)
            elif data == "events":
                await self.show_events_menu(update, context)
            elif data == "vip":
                await self.show_vip_menu(update, context)
            elif data == "daily_bonus":
                await self.handle_daily_bonus(update, context)
            elif data.startswith("buy_business_"):
                business_type = data.split("_")[-1]
                await self.buy_business(update, context, business_type)
            elif data.startswith("collect_business_"):
                business_id = int(data.split("_")[-1])
                await self.collect_business(update, context, business_id)
            # Add more callback handlers...
    
    async def buy_business(self, update: Update, context: ContextTypes.DEFAULT_TYPE, business_type: str):
        """Handle business purchase"""
        query = update.callback_query
        user = query.from_user
        
        with app.app_context():
            player = Player.query.filter_by(user_id=user.id).first()
            
            if not player:
                await query.edit_message_text(
                    self.localization.get_text('not_registered')
                )
                return
            
            business_config = Config.BUSINESS_TYPES.get(business_type)
            if not business_config:
                await query.edit_message_text("❌ Неизвестный тип бизнеса!")
                return
            
            cost = business_config['cost']
            
            if player.coins < cost:
                await query.edit_message_text(
                    f"❌ Недостаточно монет! Нужно: {cost}, у вас: {player.coins}"
                )
                return
            
            # Purchase business
            player.coins -= cost
            player.total_spent += cost
            
            business = Business(
                owner_id=player.id,
                business_type=business_type
            )
            db.session.add(business)
            
            # Add transaction record
            transaction = Transaction(
                player_id=player.id,
                transaction_type="expense",
                amount=cost,
                description=f"Покупка {business_type}"
            )
            db.session.add(transaction)
            
            db.session.commit()
            
            await query.edit_message_text(
                f"✅ Вы успешно купили {business_type}!\n"
                f"💰 Потрачено: {cost} монет\n"
                f"💰 Осталось: {player.coins} монет"
            )
            
            # Show business menu again after 2 seconds
            await asyncio.sleep(2)
            await self.show_business_menu(update, context)
    
    async def collect_business(self, update: Update, context: ContextTypes.DEFAULT_TYPE, business_id: int):
        """Handle business income collection"""
        query = update.callback_query
        user = query.from_user
        
        with app.app_context():
            business = Business.query.get(business_id)
            
            if not business or business.owner.user_id != user.id:
                await query.edit_message_text("❌ Бизнес не найден!")
                return
            
            income = business.calculate_income()
            
            if income <= 0:
                await query.edit_message_text("❌ Нет дохода для сбора!")
                return
            
            # Collect income
            business.owner.coins += income
            business.owner.total_earned += income
            business.last_collection = datetime.utcnow()
            
            # Add transaction record
            transaction = Transaction(
                player_id=business.owner.id,
                transaction_type="income",
                amount=income,
                description=f"Доход с {business.business_type}"
            )
            db.session.add(transaction)
            
            db.session.commit()
            
            await query.edit_message_text(
                f"✅ Собрано {income} монет с {business.business_type}!\n"
                f"💰 Всего монет: {business.owner.coins}"
            )
            
            # Show business menu again after 2 seconds
            await asyncio.sleep(2)
            await self.show_business_menu(update, context)
    
    # Additional methods would be implemented here...
    # This is a comprehensive foundation for the Telegram bot
    
    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown commands"""
        await update.message.reply_text(
            self.localization.get_text('unknown_command')
        )
    
    async def precheckout_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle payment pre-checkout"""
        query = update.pre_checkout_query
        await query.answer(ok=True)
        
        # Process payment with payment system
        await self.payment_system.process_payment(query, update, context)

# Additional placeholder methods that would be fully implemented
    async def show_main_menu(self, update, context):
        # Implementation for main menu
        pass
    
    async def show_profile(self, update, context):
        # Implementation for profile display
        pass
    
    async def show_farm_menu(self, update, context):
        # Implementation for farm menu
        pass
    
    async def show_pvp_menu(self, update, context):
        # Implementation for PvP menu
        pass
    
    async def show_leaderboard(self, update, context):
        # Implementation for leaderboard
        pass
    
    async def show_events_menu(self, update, context):
        # Implementation for events menu
        pass
    
    async def show_vip_menu(self, update, context):
        # Implementation for VIP menu
        pass
    
    async def handle_daily_bonus(self, update, context):
        # Implementation for daily bonus
        pass
    
    async def help_command(self, update, context):
        # Implementation for help command
        pass
    
    async def farm_command(self, update, context):
        # Implementation for farm command
        pass
    
    async def pvp_command(self, update, context):
        # Implementation for PvP command
        pass
    
    async def leaderboard_command(self, update, context):
        # Implementation for leaderboard command
        pass
    
    async def events_command(self, update, context):
        # Implementation for events command
        pass
    
    async def vip_command(self, update, context):
        # Implementation for VIP command
        pass
    
    async def daily_bonus_command(self, update, context):
        # Implementation for daily bonus command
        pass
