import os
import csv
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# ============================================
# ⚙️ الإعدادات
# ============================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CSV_FILE_PATH = '1XBetCrash.csv'
JSON_FILE_PATH = 'scraped_data.json'
DATA_BACKUP_PATH = 'data_backup.csv'

# معرف الحساب API
API_ACCOUNT = "AAEcsa25t4r0BjKb3koW67OmLBQ_22xVloA:8610233048"

# ============================================
# 📊 فئات البيانات
# ============================================

@dataclass
class BetRecord:
    """تسجيل الرهان"""
    time: str
    players: int
    total_bets: str
    multiplier: float
    total_gains: str
    
    def to_dict(self):
        return {
            'time': self.time,
            'players': self.players,
            'total_bets': self.total_bets,
            'multiplier': self.multiplier,
            'total_gains': self.total_gains
        }

# ============================================
# 💾 إدارة البيانات
# ============================================

class DataManager:
    """مدير البيانات المتقدم"""
    
    def __init__(self, csv_path: str = CSV_FILE_PATH):
        self.csv_path = csv_path
        self.json_path = JSON_FILE_PATH
        self.backup_path = DATA_BACKUP_PATH
        self.cache = []
        self.last_update = None
        self.api_account = API_ACCOUNT
        self.load_data()
    
    def load_data(self) -> List[Dict]:
        """تحميل البيانات من CSV"""
        try:
            if not os.path.exists(self.csv_path):
                logger.warning(f"ملف {self.csv_path} غير موجود")
                return []
            
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                self.cache = list(reader)
                self.last_update = datetime.now()
                logger.info(f"تم تحميل {len(self.cache)} سجل من البيانات")
                logger.info(f"معرف الحساب: {self.api_account}")
                return self.cache
        except Exception as e:
            logger.error(f"خطأ في تحميل البيانات: {e}")
            return []
    
    def get_latest_bet(self) -> Optional[Dict]:
        """الحصول على آخر رهان"""
        if self.cache:
            return self.cache[-1]
        return None
    
    def get_all_bets(self) -> List[Dict]:
        """الحصول على جميع الرهانات"""
        return self.cache
    
    def get_recent_bets(self, limit: int = 10) -> List[Dict]:
        """الحصول على آخر N رهان"""
        return self.cache[-limit:] if self.cache else []
    
    def calculate_stats(self) -> Optional[Dict]:
        """حساب الإحصائيات المتقدمة"""
        try:
            if not self.cache:
                return None
            
            # تحويل البيانات
            players_list = []
            multipliers = []
            
            for row in self.cache:
                try:
                    players = int(row.get('Number of players', 0))
                    multiplier = float(row.get('Multiplier(Crash)', 0))
                    players_list.append(players)
                    multipliers.append(multiplier)
                except (ValueError, KeyError):
                    continue
            
            if not multipliers:
                return None
            
            stats = {
                'total_bets': len(self.cache),
                'avg_players': sum(players_list) / len(players_list) if players_list else 0,
                'max_players': max(players_list) if players_list else 0,
                'min_players': min(players_list) if players_list else 0,
                'avg_multiplier': sum(multipliers) / len(multipliers),
                'max_multiplier': max(multipliers),
                'min_multiplier': min(multipliers),
                'crash_count': sum(1 for m in multipliers if m < 1.5),
                'high_multiplier_count': sum(1 for m in multipliers if m >= 3),
                'api_account': self.api_account,
                'last_update': self.last_update.isoformat() if self.last_update else None
            }
            return stats
        except Exception as e:
            logger.error(f"خطأ في حساب الإحصائيات: {e}")
            return None
    
    def get_best_performance(self) -> Optional[Dict]:
        """أفضل أداء"""
        if not self.cache:
            return None
        try:
            best = max(self.cache, key=lambda x: float(x.get('Multiplier(Crash)', 0)))
            return best
        except Exception as e:
            logger.error(f"خطأ في الحصول على أفضل أداء: {e}")
            return None
    
    def get_worst_performance(self) -> Optional[Dict]:
        """أسوأ أداء"""
        if not self.cache:
            return None
        try:
            worst = min(self.cache, key=lambda x: float(x.get('Multiplier(Crash)', 0)))
            return worst
        except Exception as e:
            logger.error(f"خطأ في الحصول على أسوأ أداء: {e}")
            return None
    
    def export_to_json(self) -> bool:
        """تصدير البيانات إلى JSON"""
        try:
            stats = self.calculate_stats()
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'api_account': self.api_account,
                'statistics': stats,
                'latest_bet': self.get_latest_bet(),
                'recent_bets': self.get_recent_bets(20),
                'total_records': len(self.cache)
            }
            
            with open(self.json_path, 'w', encoding='utf-8') as file:
                json.dump(export_data, file, ensure_ascii=False, indent=2)
            
            logger.info(f"تم تصدير البيانات إلى {self.json_path}")
            return True
        except Exception as e:
            logger.error(f"خطأ في تصدير JSON: {e}")
            return False
    
    def refresh(self) -> bool:
        """تحديث البيانات"""
        self.load_data()
        return self.export_to_json()

# ============================================
# 🤖 معالجات البوت
# ============================================

class BotHandlers:
    """معالجات البوت المتقدمة"""
    
    def __init__(self, data_manager: DataManager):
        self.dm = data_manager
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج /start"""
        keyboard = [
            [InlineKeyboardButton("📊 آخر رهان", callback_data='latest')],
            [InlineKeyboardButton("📈 الإحصائيات", callback_data='stats')],
            [InlineKeyboardButton("📋 آخر 10 رهانات", callback_data='recent')],
            [InlineKeyboardButton("🏆 أفضل أداء", callback_data='best')],
            [InlineKeyboardButton("📉 أسوأ أداء", callback_data='worst')],
            [InlineKeyboardButton("🔄 تحديث البيانات", callback_data='refresh')],
            [InlineKeyboardButton("🔐 معرف الحساب", callback_data='account')],
            [InlineKeyboardButton("❓ المساعدة", callback_data='help')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = f"""
🎮 *مرحباً بك في بوت 1XBET Crash المتطور!* 🎮

ℹ️ *معرف الحساب:* `{self.dm.api_account}`

هذا البوت يوفر لك:
✅ معلومات الرهانات الحية والمحدثة
✅ إحصائيات تفصيلية ومتقدمة
✅ تحليل شامل للأداء
✅ بيانات دقيقة من 1XBET
✅ تصدير البيانات بصيغ متعددة
✅ واجهة سهلة وسريعة
✅ دعم كامل للعربية

اختر من الخيارات أدناه:
        """
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def latest_bet(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """عرض آخر رهان"""
        try:
            latest = self.dm.get_latest_bet()
            
            if not latest:
                await update.message.reply_text("❌ لا توجد بيانات متاحة حالياً")
                return
            
            message = f"""
📊 *آخر رهان:*
━━━━━━━━━━━━━━━━━━━━━━━
🔐 المعرف: `{self.dm.api_account}`
⏰ الوقت: `{latest.get('Time', 'N/A')}`
👥 عدد اللاعبين: `{latest.get('Number of players', 'N/A')}`
💰 إجمالي الرهانات: `{latest.get('Total bets', 'N/A')}`
📈 المضاعف: `{latest.get('Multiplier(Crash)', 'N/A')}`
🎯 الأرباح الكلية: `{latest.get('Total gains', 'N/A')}`
━━━━━━━━━━━━━━━━━━━━━━━
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"خطأ في latest_bet: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """عرض الإحصائيات المتقدمة"""
        try:
            stats = self.dm.calculate_stats()
            
            if not stats:
                await update.message.reply_text("❌ لا توجد بيانات كافية")
                return
            
            message = f"""
📈 *الإحصائيات المتقدمة:*
━━━━━━━━━━━━━━━━━━━━━━━
🔐 المعرف: `{stats['api_account']}`
━━━━━━━━━━━━━━━━━━━━━━━
📊 عدد الرهانات: `{stats['total_bets']}`
👥 متوسط اللاعبين: `{stats['avg_players']:.0f}`
🔝 أقصى عدد لاعبين: `{stats['max_players']}`
📉 أقل عدد لاعبين: `{stats['min_players']}`
━━━━━━━━━━━━━━━━━━━━━━━
📈 أعلى مضاعف: `{stats['max_multiplier']:.2f}`
📉 أقل مضاعف: `{stats['min_multiplier']:.2f}`
📊 متوسط المضاعف: `{stats['avg_multiplier']:.2f}`
━━━━━━━━━━━━━━━━━━━━━━━
💥 عدد الكراشات: `{stats['crash_count']}`
🚀 عدد المضاعفات العالية (3+): `{stats['high_multiplier_count']}`
━━━━━━━━━━━━━━━━━━━━━━━
⏰ آخر تحديث: `{stats['last_update']}`
━━━━━━━━━━━━━━━━━━━━━━━
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"خطأ في statistics: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def recent_bets(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """عرض آخر 10 رهانات"""
        try:
            bets = self.dm.get_recent_bets(10)
            
            if not bets:
                await update.message.reply_text("❌ لا توجد بيانات")
                return
            
            header = f"📊 *آخر 10 رهانات - {self.dm.api_account}:*\n"
            header += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            header += "`رقم | الوقت | المضاعف | اللاعبين`\n"
            header += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            data_str = header
            for i, bet in enumerate(bets, 1):
                time = bet.get('Time', 'N/A')
                multiplier = bet.get('Multiplier(Crash)', 'N/A')
                players = bet.get('Number of players', 'N/A')
                data_str += f"`{i:2d} | {time} | {multiplier} | {players}`\n"
            
            await update.message.reply_text(data_str, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"خطأ في recent_bets: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def best_performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """أفضل أداء"""
        try:
            best = self.dm.get_best_performance()
            
            if not best:
                await update.message.reply_text("❌ لا توجد بيانات")
                return
            
            message = f"""
🏆 *أفضل أداء:*
━━━━━━━━━━━━━━━━━━━━━━━
🔐 المعرف: `{self.dm.api_account}`
⏰ الوقت: `{best.get('Time', 'N/A')}`
👥 عدد اللاعبين: `{best.get('Number of players', 'N/A')}`
💰 إجمالي الرهانات: `{best.get('Total bets', 'N/A')}`
📈 المضاعف: `{best.get('Multiplier(Crash)', 'N/A')}` 🚀
🎯 الأرباح: `{best.get('Total gains', 'N/A')}`
━━━━━━━━━━━━━━━━━━━━━━━
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"خطأ في best_performance: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def worst_performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """أسوأ أداء"""
        try:
            worst = self.dm.get_worst_performance()
            
            if not worst:
                await update.message.reply_text("❌ لا توجد بيانات")
                return
            
            message = f"""
📉 *أسوأ أداء:*
━━━━━━━��━━━━━━━━━━━━━━━
🔐 المعرف: `{self.dm.api_account}`
⏰ الوقت: `{worst.get('Time', 'N/A')}`
👥 عدد اللاعبين: `{worst.get('Number of players', 'N/A')}`
💰 إجمالي الرهانات: `{worst.get('Total bets', 'N/A')}`
📉 المضاعف: `{worst.get('Multiplier(Crash)', 'N/A')}`
🎯 الأرباح: `{worst.get('Total gains', 'N/A')}`
━━━━━━━━━━━━━━━━━━━━━━━
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"خطأ في worst_performance: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def refresh_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """تحديث البيانات"""
        try:
            await update.message.reply_text("🔄 جاري تحديث البيانات...")
            
            success = self.dm.refresh()
            
            if success:
                stats = self.dm.calculate_stats()
                message = f"""
✅ *تم تحديث البيانات بنجاح!*
━━━━━━━━━━━━━━━━━━━━━━━
🔐 المعرف: `{self.dm.api_account}`
📊 عدد الرهانات: `{stats['total_bets'] if stats else 0}`
⏰ آخر تحديث: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`
━━━━━━━━━━━━━━━━━━━━━━━
                """
                await update.message.reply_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ فشل تحديث البيانات")
        except Exception as e:
            logger.error(f"خطأ في refresh_data: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def account_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """عرض معلومات الحساب"""
        try:
            stats = self.dm.calculate_stats()
            
            account_message = f"""
🔐 *معلومات الحساب:*
━━━━━━━━━━━━━━━━━━━━━━━
📱 المعرف الكامل:
`{self.dm.api_account}`

📊 *الإحصائيات:*
━━━━━━━━━━━━━━━━━━━━━━━
📈 عدد الرهانات: `{stats['total_bets'] if stats else 0}`
👥 متوسط اللاعبين: `{stats['avg_players']:.0f if stats else 0}`
📊 متوسط المضاعف: `{stats['avg_multiplier']:.2f if stats else 0}`
🎯 أفضل مضاعف: `{stats['max_multiplier']:.2f if stats else 0}`

⏰ *معلومات التحديث:*
━━━━━━━━━━━━━━━━━━━━━━━
آخر تحديث: `{self.dm.last_update.strftime('%Y-%m-%d %H:%M:%S') if self.dm.last_update else 'غير محدث'}`
━━━━━━━━━━━━━━━━━━━━━━━
            """
            
            await update.message.reply_text(account_message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"خطأ في account_info: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """عرض المساعدة"""
        help_text = f"""
🆘 *المساعدة:*
━━━━━━━━━━━━━━━━━━━━━━━

🔐 *معرف حسابك:*
`{self.dm.api_account}`

*الأوامر المتاحة:*
/start - ابدأ البوت 🚀
/latest - آخر رهان 📊
/stats - الإحصائيات 📈
/recent - آخر 10 رهانات 📋
/best - أفضل أداء 🏆
/worst - أسوأ أداء 📉
/account - معلومات ��لحساب 🔐
/refresh - تحديث البيانات 🔄
/help - المساعدة ❓

*الميزات المتقدمة:*
✅ جلب البيانات من 1XBetCrash.csv
✅ إحصائيات متقدمة وتحليلات
✅ تصدير البيانات JSON
✅ تحديث فوري للبيانات
✅ واجهة سهلة وسريعة
✅ دعم العربية كاملاً
✅ معرف حساب فريد

*معلومات إضافية:*
📁 ملف CSV: 1XBetCrash.csv
📋 ملف JSON: scraped_data.json
🔐 آمن وموثوق 100%

━━━━━━━━━━━━━━━━━━━━━━━
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج الأزرار"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        
        if callback_data == 'latest':
            await self.latest_bet(query, context)
        elif callback_data == 'stats':
            await self.statistics(query, context)
        elif callback_data == 'recent':
            await self.recent_bets(query, context)
        elif callback_data == 'best':
            await self.best_performance(query, context)
        elif callback_data == 'worst':
            await self.worst_performance(query, context)
        elif callback_data == 'refresh':
            await self.refresh_data(query, context)
        elif callback_data == 'account':
            await self.account_info(query, context)
        elif callback_data == 'help':
            await self.help_command(query, context)

# ============================================
# 🚀 بدء التطبيق
# ============================================

async def main():
    """بدء البوت المتطور"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ لم يتم تعيين TELEGRAM_BOT_TOKEN!")
        logger.error("أضف التوكن في ملف .env")
        return
    
    # إنشاء مدير البيانات
    data_manager = DataManager(CSV_FILE_PATH)
    bot_handlers = BotHandlers(data_manager)
    
    # إنشاء التطبيق
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", bot_handlers.start))
    application.add_handler(CommandHandler("latest", bot_handlers.latest_bet))
    application.add_handler(CommandHandler("stats", bot_handlers.statistics))
    application.add_handler(CommandHandler("recent", bot_handlers.recent_bets))
    application.add_handler(CommandHandler("best", bot_handlers.best_performance))
    application.add_handler(CommandHandler("worst", bot_handlers.worst_performance))
    application.add_handler(CommandHandler("account", bot_handlers.account_info))
    application.add_handler(CommandHandler("refresh", bot_handlers.refresh_data))
    application.add_handler(CommandHandler("help", bot_handlers.help_command))
    
    # معالج الأزرار
    application.add_handler(CallbackQueryHandler(bot_handlers.button_callback))
    
    logger.info("=" * 70)
    logger.info("🚀 بوت 1XBET Crash المتطور يعمل الآن!")
    logger.info("=" * 70)
    logger.info(f"🔐 معرف الحساب: {API_ACCOUNT}")
    logger.info(f"📁 ملف البيانات: {CSV_FILE_PATH}")
    logger.info(f"📋 ملف JSON: {JSON_FILE_PATH}")
    logger.info(f"📊 عدد الرهانات المحملة: {len(data_manager.cache)}")
    logger.info("=" * 70)
    
    # بدء البوت
    await application.run_polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 تم إيقاف البوت")
    except Exception as e:
        logger.error(f"❌ خطأ في البوت: {e}")
