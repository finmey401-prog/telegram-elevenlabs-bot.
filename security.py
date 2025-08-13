import logging
import time
from datetime import datetime, timedelta
from collections import defaultdict
from main import app, db
from models import PlayerActivity, Player
from config import Config
import json

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self):
        self.rate_limits = defaultdict(list)  # user_id -> list of timestamps
        self.suspicious_activities = defaultdict(int)  # user_id -> activity count
        self.blocked_users = set()
        
    def check_rate_limit(self, user_id, max_actions=None):
        """Check if user is within rate limits"""
        if max_actions is None:
            max_actions = Config.MAX_ACTIONS_PER_MINUTE
        
        current_time = time.time()
        
        # Remove old timestamps (older than 1 minute)
        self.rate_limits[user_id] = [
            timestamp for timestamp in self.rate_limits[user_id] 
            if current_time - timestamp < 60
        ]
        
        # Check if user exceeded rate limit
        if len(self.rate_limits[user_id]) >= max_actions:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False
        
        # Add current timestamp
        self.rate_limits[user_id].append(current_time)
        return True
    
    def log_player_activity(self, user_id, action, details=None):
        """Log player activity for analysis"""
        try:
            with app.app_context():
                activity = PlayerActivity(
                    player_id=self.get_player_id_from_user_id(user_id),
                    action_type=action,
                    details=json.dumps(details) if details else None
                )
                
                db.session.add(activity)
                db.session.commit()
                
                # Check for suspicious patterns
                self.detect_suspicious_activity(user_id, action)
                
        except Exception as e:
            logger.error(f"Error logging player activity: {e}")
            db.session.rollback()
    
    def get_player_id_from_user_id(self, user_id):
        """Get player ID from Telegram user ID"""
        player = Player.query.filter_by(user_id=user_id).first()
        return player.id if player else None
    
    def detect_suspicious_activity(self, user_id, action):
        """Detect patterns that might indicate cheating"""
        suspicious_actions = [
            'collect_business',
            'harvest_crop',
            'pvp_attack',
            'buy_business'
        ]
        
        if action in suspicious_actions:
            current_time = time.time()
            
            # Count recent activities
            recent_activities = [
                timestamp for timestamp in self.rate_limits[user_id]
                if current_time - timestamp < 300  # Last 5 minutes
            ]
            
            if len(recent_activities) > Config.SUSPICIOUS_ACTIVITY_THRESHOLD:
                self.flag_suspicious_user(user_id, f"High activity rate: {len(recent_activities)} actions in 5 minutes")
    
    def flag_suspicious_user(self, user_id, reason):
        """Flag user for suspicious activity"""
        self.suspicious_activities[user_id] += 1
        
        logger.warning(f"Suspicious activity flagged for user {user_id}: {reason}")
        
        # Auto-block if too many flags
        if self.suspicious_activities[user_id] >= 5:
            self.block_user(user_id, f"Auto-blocked: {reason}")
    
    def block_user(self, user_id, reason):
        """Block user from game actions"""
        self.blocked_users.add(user_id)
        
        try:
            with app.app_context():
                player = Player.query.filter_by(user_id=user_id).first()
                if player:
                    # Log the block
                    activity = PlayerActivity(
                        player_id=player.id,
                        action_type="user_blocked",
                        details=json.dumps({"reason": reason})
                    )
                    db.session.add(activity)
                    db.session.commit()
                    
                    logger.critical(f"User {user_id} ({player.username}) has been blocked: {reason}")
                    
        except Exception as e:
            logger.error(f"Error blocking user: {e}")
    
    def is_user_blocked(self, user_id):
        """Check if user is blocked"""
        return user_id in self.blocked_users
    
    def validate_transaction_amount(self, amount, transaction_type):
        """Validate if transaction amount is reasonable"""
        max_amounts = {
            'income': 1000000,  # Max income per transaction
            'expense': 500000,  # Max expense per transaction
            'pvp_win': 50000,   # Max PvP win
            'pvp_loss': 50000   # Max PvP loss
        }
        
        max_amount = max_amounts.get(transaction_type, 100000)
        
        if amount > max_amount:
            logger.warning(f"Suspicious transaction amount: {amount} for type {transaction_type}")
            return False
        
        return True
    
    def detect_coin_generation_exploit(self, player_id):
        """Detect unrealistic coin generation patterns"""
        try:
            with app.app_context():
                player = Player.query.get(player_id)
                if not player:
                    return False
                
                # Check account age vs wealth
                account_age_hours = (datetime.utcnow() - player.created_at).total_seconds() / 3600
                
                if account_age_hours > 0:
                    wealth_per_hour = player.coins / account_age_hours
                    
                    # Flag if earning more than reasonable amount per hour
                    if wealth_per_hour > 20000:  # 20k coins per hour is suspicious
                        self.flag_suspicious_user(
                            player.user_id, 
                            f"Unrealistic wealth accumulation: {wealth_per_hour:.0f} coins/hour"
                        )
                        return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error detecting coin generation exploit: {e}")
            return False
    
    def validate_business_income(self, business, claimed_income):
        """Validate if business income claim is legitimate"""
        from config import Config
        
        business_config = Config.BUSINESS_TYPES.get(business.business_type)
        if not business_config:
            return False
        
        # Calculate maximum possible income
        base_income = business_config['income'] * business.level
        collection_time = business_config['time']
        
        time_passed = (datetime.utcnow() - business.last_collection).total_seconds()
        max_collections = int(time_passed / collection_time)
        
        # Allow some margin for VIP bonuses (up to 3x)
        max_income = base_income * max_collections * 3
        
        if claimed_income > max_income:
            logger.warning(f"Suspicious business income claim: {claimed_income} vs max {max_income}")
            self.flag_suspicious_user(
                business.owner.user_id,
                f"Invalid business income: claimed {claimed_income}, max {max_income}"
            )
            return False
        
        return True
    
    def analyze_player_behavior(self, user_id, days=7):
        """Analyze player behavior patterns over time"""
        try:
            with app.app_context():
                player_id = self.get_player_id_from_user_id(user_id)
                if not player_id:
                    return {}
                
                # Get activities from last N days
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                activities = PlayerActivity.query.filter(
                    PlayerActivity.player_id == player_id,
                    PlayerActivity.timestamp >= cutoff_date
                ).all()
                
                # Analyze patterns
                action_counts = defaultdict(int)
                hourly_distribution = defaultdict(int)
                
                for activity in activities:
                    action_counts[activity.action_type] += 1
                    hourly_distribution[activity.timestamp.hour] += 1
                
                # Calculate statistics
                total_actions = sum(action_counts.values())
                peak_hour = max(hourly_distribution.keys(), key=hourly_distribution.get) if hourly_distribution else 0
                
                analysis = {
                    'total_actions': total_actions,
                    'actions_per_day': total_actions / days,
                    'action_breakdown': dict(action_counts),
                    'peak_activity_hour': peak_hour,
                    'hourly_distribution': dict(hourly_distribution),
                    'is_suspicious': total_actions > (days * 200)  # More than 200 actions per day
                }
                
                return analysis
                
        except Exception as e:
            logger.error(f"Error analyzing player behavior: {e}")
            return {}
    
    def get_security_report(self):
        """Generate security report for administrators"""
        try:
            with app.app_context():
                report = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'blocked_users': len(self.blocked_users),
                    'flagged_users': len(self.suspicious_activities),
                    'rate_limited_users': len([uid for uid, actions in self.rate_limits.items() if len(actions) > 0]),
                    'top_suspicious_users': sorted(
                        self.suspicious_activities.items(), 
                        key=lambda x: x[1], 
                        reverse=True
                    )[:10]
                }
                
                # Add player statistics
                total_players = Player.query.count()
                new_players_today = Player.query.filter(
                    Player.created_at >= datetime.utcnow().date()
                ).count()
                
                report['player_stats'] = {
                    'total_players': total_players,
                    'new_today': new_players_today,
                    'active_today': len(set(self.rate_limits.keys()))
                }
                
                return report
                
        except Exception as e:
            logger.error(f"Error generating security report: {e}")
            return {}
    
    def cleanup_old_data(self):
        """Clean up old security data"""
        current_time = time.time()
        
        # Clean rate limits older than 1 hour
        for user_id in list(self.rate_limits.keys()):
            self.rate_limits[user_id] = [
                timestamp for timestamp in self.rate_limits[user_id]
                if current_time - timestamp < 3600
            ]
            
            if not self.rate_limits[user_id]:
                del self.rate_limits[user_id]
        
        # Reset suspicious activity counters daily
        if hasattr(self, 'last_cleanup'):
            if current_time - self.last_cleanup > 86400:  # 24 hours
                self.suspicious_activities.clear()
                self.last_cleanup = current_time
        else:
            self.last_cleanup = current_time
    
    def unblock_user(self, user_id, admin_user_id=None):
        """Unblock a user (admin action)"""
        if user_id in self.blocked_users:
            self.blocked_users.remove(user_id)
            
            try:
                with app.app_context():
                    player_id = self.get_player_id_from_user_id(user_id)
                    if player_id:
                        activity = PlayerActivity(
                            player_id=player_id,
                            action_type="user_unblocked",
                            details=json.dumps({"admin_user_id": admin_user_id})
                        )
                        db.session.add(activity)
                        db.session.commit()
                        
                        logger.info(f"User {user_id} has been unblocked by admin {admin_user_id}")
                        return True
                        
            except Exception as e:
                logger.error(f"Error unblocking user: {e}")
        
        return False
