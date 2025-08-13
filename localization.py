import logging

logger = logging.getLogger(__name__)

class Localization:
    def __init__(self, language='ru'):
        self.language = language
        self.texts = {
            'ru': {
                # Welcome messages
                'welcome_new_player': "🎉 Добро пожаловать, {username}!\n\nВы начинаете с {coins} монет. Постройте свою экономическую империю!",
                'welcome_back': "👋 С возвращением, {username}!\n\nВыберите действие из меню ниже:",
                'not_registered': "❌ Вы не зарегистрированы. Нажмите /start для начала игры.",
                
                # Profile information
                'profile_info': """
<b>👤 Профиль игрока</b>

<b>Имя:</b> {username}
<b>Уровень:</b> {level}
<b>Монеты:</b> 💰 {coins:,}
<b>Энергия:</b> ⚡ {energy}
<b>Бизнесы:</b> 🏢 {total_businesses}
<b>Фермы:</b> 🚜 {total_farms}

<b>PvP статистика:</b>
• Побед: {pvp_wins}
• Поражений: {pvp_losses}

<b>VIP статус:</b> {vip_status}
                """,
                
                # Business messages
                'business_menu_title': "🏢 <b>Управление бизнесом</b>",
                'no_businesses': "У вас пока нет бизнесов.",
                'available_businesses': "\n<b>Доступные бизнесы:</b>",
                'business_income_ready': "💰 Доступно: {income} монет",
                'insufficient_coins': "❌ Недостаточно монет! Нужно: {needed}, у вас: {current}",
                'business_purchased': "✅ Вы успешно купили {business_type}!\n💰 Потрачено: {cost} монет\n💰 Осталось: {coins} монет",
                'income_collected': "✅ Собрано {income} монет с {business_type}!\n💰 Всего монет: {total_coins}",
                'no_income_available': "❌ Нет дохода для сбора!",
                'business_not_found': "❌ Бизнес не найден!",
                
                # Farm messages
                'farm_menu_title': "🚜 <b>Управление фермой</b>",
                'crop_planted': "✅ Посажено {crop_type}! Урожай будет готов через {time}.",
                'crop_harvested': "✅ Собран урожай {crop_type}! Получено {amount} монет.",
                'crop_not_ready': "❌ Урожай еще не готов!",
                'farm_slots_full': "❌ Все слоты заняты!",
                'insufficient_energy': "❌ Недостаточно энергии!",
                
                # PvP messages
                'pvp_menu_title': "⚔️ <b>PvP Сражения</b>",
                'attack_successful': "🎉 Победа! Украдено {amount} монет у {opponent}!",
                'attack_failed': "💥 Поражение! Ваша атака была отражена.",
                'cannot_attack_self': "❌ Нельзя атаковать самого себя!",
                'target_too_weak': "❌ Нельзя атаковать игроков намного слабее вас!",
                'target_no_coins': "❌ У защитника слишком мало монет для атаки!",
                'attack_cooldown': "❌ Атака будет доступна через {seconds} секунд!",
                
                # Events messages
                'events_menu_title': "🎪 <b>Текущие события</b>",
                'no_active_events': "В данный момент нет активных событий.",
                'event_time_left': "Осталось: {time_left}",
                
                # VIP messages
                'vip_menu_title': "💎 <b>VIP Подписка</b>",
                'vip_benefits': "VIP дает следующие преимущества:",
                'vip_active': "✅ VIP активен до: {expires_at}",
                'vip_expired': "❌ VIP подписка истекла",
                
                # Daily bonus
                'daily_bonus_claimed': "🎁 Получен ежедневный бонус: {amount} монет!",
                'daily_bonus_not_available': "❌ Ежедневный бонус уже получен! Возвращайтесь завтра.",
                
                # Leaderboard
                'leaderboard_title': "🏆 <b>Таблица лидеров</b>",
                'leaderboard_coins': "💰 По монетам:",
                'leaderboard_level': "📊 По уровню:",
                'leaderboard_pvp': "⚔️ По PvP победам:",
                
                # Error messages
                'unknown_command': "❓ Неизвестная команда. Используйте /help для получения помощи.",
                'rate_limit_exceeded': "⚠️ Слишком много действий! Подождите немного.",
                'maintenance_mode': "🔧 Идет техническое обслуживание. Попробуйте позже.",
                'database_error': "❌ Ошибка базы данных. Попробуйте позже.",
                
                # Help messages
                'help_text': """
<b>🎮 Помощь по игре</b>

<b>Основные команды:</b>
/start - Начать игру
/profile - Ваш профиль
/business - Управление бизнесом
/farm - Управление фермой
/pvp - PvP сражения
/leaderboard - Таблица лидеров
/events - Текущие события
/vip - VIP подписка
/daily - Ежедневный бонус

<b>Как играть:</b>
1. Развивайте бизнес для получения дохода
2. Выращивайте урожай на ферме
3. Участвуйте в PvP для получения монет других игроков
4. Улучшайте свои постройки
5. Участвуйте в событиях для получения бонусов

<b>Энергия:</b>
Энергия восстанавливается со временем и нужна для действий.

<b>VIP подписка:</b>
Дает дополнительную энергию, увеличивает доходы и ускоряет процессы.
                """,
                
                # Time formatting
                'time_minutes': "{minutes} минут",
                'time_hours': "{hours} часов",
                'time_days': "{days} дней",
                
                # Numbers formatting
                'level_short': "ур. {level}",
                'coins_short': "{coins:,} монет",
                'energy_short': "{energy} энергии",
            }
        }
    
    def get_text(self, key, **kwargs):
        """Get localized text with formatting"""
        try:
            text = self.texts.get(self.language, {}).get(key, f"Missing: {key}")
            
            if kwargs:
                return text.format(**kwargs)
            return text
            
        except Exception as e:
            logger.error(f"Error formatting text '{key}': {e}")
            return f"Error: {key}"
    
    def format_time_remaining(self, seconds):
        """Format time remaining in human readable format"""
        if seconds < 60:
            return self.get_text('time_minutes', minutes=1)
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return self.get_text('time_minutes', minutes=minutes)
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return self.get_text('time_hours', hours=hours)
        else:
            days = int(seconds / 86400)
            return self.get_text('time_days', days=days)
    
    def format_number(self, number):
        """Format large numbers for display"""
        if number >= 1000000:
            return f"{number/1000000:.1f}М"
        elif number >= 1000:
            return f"{number/1000:.1f}К"
        else:
            return str(number)
    
    def format_crop_name(self, crop_type):
        """Get localized crop name"""
        crop_names = {
            'wheat': 'Пшеница',
            'corn': 'Кукуруза', 
            'potato': 'Картофель',
            'tomato': 'Помидоры'
        }
        return crop_names.get(crop_type, crop_type.capitalize())
    
    def format_business_name(self, business_type):
        """Get localized business name"""
        business_names = {
            'cafe': 'Кафе',
            'shop': 'Магазин',
            'factory': 'Фабрика',
            'bank': 'Банк'
        }
        return business_names.get(business_type, business_type.capitalize())
    
    def format_vip_type(self, vip_type):
        """Get localized VIP type name"""
        vip_names = {
            'basic': 'Базовый',
            'premium': 'Премиум',
            'ultimate': 'Ультимативный'
        }
        return vip_names.get(vip_type, vip_type.capitalize())
    
    def get_random_greeting(self):
        """Get random greeting message"""
        import random
        
        greetings = [
            "Привет, предприниматель! 👋",
            "Добро пожаловать в игру! 🎮",
            "Время строить империю! 🏗️",
            "Готовы к новым достижениям? 🚀",
            "Удачной торговли! 💼"
        ]
        
        return random.choice(greetings)
    
    def get_random_success_message(self):
        """Get random success message"""
        import random
        
        messages = [
            "Отлично! 👍",
            "Великолепно! ✨",
            "Прекрасная работа! 🎉",
            "Так держать! 💪",
            "Успех! 🏆"
        ]
        
        return random.choice(messages)
    
    def add_custom_text(self, key, text):
        """Add custom localized text"""
        if self.language not in self.texts:
            self.texts[self.language] = {}
        
        self.texts[self.language][key] = text
    
    def set_language(self, language):
        """Set localization language"""
        self.language = language
        logger.info(f"Language set to: {language}")
