import os
import csv
import json
import asyncio
import logging
import aiohttp
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
API_ACCOUNT = "AAEcsa25t4r0BjKb3koW67OmLBQ_22xVloA:8610233048"

# APIs للنكات
JOKE_API_URL = "https://official-joke-api.appspot.com/random_joke"
ARABIC_JOKE_API_URL = "https://official-joke-api.appspot.com/jokes/random"

# ============================================
# 😂 مدير النكات
# ============================================

class JokeManager:
    """مدير النكات المتقدم"""
    
    def __init__(self):
        self.joke_cache = []
        self.last_joke = None
        self.total_jokes_fetched = 0
    
    async def get_random_joke(self) -> Optional[Dict]:
        """الحصول على نكتة عشوائية من API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(JOKE_API_URL, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        joke = await response.json()
                        self.last_joke = joke
                        self.total_jokes_fetched += 1
                        self.joke_cache.append(joke)
                        
                        # الاحتفاظ بـ آخر 50 نكتة فقط
                        if len(self.joke_cache) > 50:
                            self.joke_cache.pop(0)
                        
                        logger.info(f"تم جلب نكتة جديدة: {joke.get('setup', '')[:50]}")
                        return joke
                    else:
                        logger.error(f"خطأ في API: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"خطأ في الحصول على النكتة: {e}")
            return None
    
    async def get_programming_joke(self) -> Optional[Dict]:
        """الحصول على نكتة برمجة"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://official-joke-api.appspot.com/jokes/programming/random",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        joke = await response.json()
                        if isinstance(joke, list):
                            joke = joke[0]
                        self.total_jokes_fetched += 1
                        return joke
                    return None
        except Exception as e:
            logger.error(f"خطأ في جلب نكتة البرمجة: {e}")
            return None
    
    async def get_knock_knock_joke(self) -> Optional[Dict]:
        """الحصول على نكتة Knock Knock"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://official-joke-api.appspot.com/jokes/knock-knock/random",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        joke = await response.json()
                        if isinstance(joke, list):
                            joke = joke[0]
                        self.total_jokes_fetched += 1
                        return joke
                    return None
        except Exception as e:
            logger.error(f"خطأ في جلب نكتة Knock Knock: {e}")
            return None
    
    def get_cached_jokes(self) -> List[Dict]:
        """الحصول على النكات المحفوظة"""
        return self.joke_cache
    
    def format_joke(self, joke: Dict) -> str:
        """تنسيق النكتة للعرض"""
        if not joke:
            return "❌ لا توجد نكتة متاحة"
        
        setup = joke.get('setup', '')
        punchline = joke.get('punchline', '')
        
        return f"""
😂 *نكتة عشوائية:*
━━━━━━━━━━━━━━━━━━━━━━━
{setup}

{punchline}
━━━━━━━━━━━━━━━━━━━━━━━
        """

# ============================================
# 💾 إدارة البيانات
# ============================================

class DataManager:
    """مدير البيانات المتقدم"""
    
    def __init__(self, csv_path: str = CSV_FILE_PATH):
        self.csv_path = csv_path
        self.json_path = JSON_FILE_PATH
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
                return self.cache
        except Exception as e:
            logger.error(f"خطأ في تحميل البيانات: {e}")
            return []
    
    def get_latest_bet(self) -> Optional[Dict]:
        """الحصول على آخر رهان"""
        if self.cache:
            return self.cache[-1]
        return None
    
    def calculate_stats(self) -> Optional[Dict]:
        """حساب الإحصائيات"""
        try:
            if not self.cache:
                return None
            
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
            
            return {
                'total_bets': len(self.cache),
                'avg_players': sum(players_list) / len(players_list) if players_list else 0,
                'max_players': max(players_list) if players_list else 0,
                'min_players': min(players_list) if players_list else 0,
                'avg_multiplier': sum(multipliers) / len(multipliers),
                'max_multiplier': max(multipliers),
                'min_multiplier': min(multipliers),
                'crash_count': sum(1 for m in multipliers if m < 1.5),
                'high_multiplier_count': sum(1 for m in multipliers if m >= 3),
            }
        except Exception as e:
            logger.error(f"خطأ في حساب الإحصائيات: {e}")
            return None

# ============================================
# 🤖 معالجات البوت
# ============================================

class BotHandlers:
    """معالجات البوت المتقدمة"""
    
    def __init__(self, data_manager: DataManager, joke_manager: JokeManager):
        self.dm = data_manager
        self.jm = joke_manager
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج /start"""
        keyboard = [
            [InlineKeyboardButton("📊 آخر رهان", callback_data='latest')],
            [InlineKeyboardButton("📈 الإحصائيات", callback_data='stats')],
            [InlineKeyboardButton("🏆 أفضل أداء", callback_data='best')],
            [InlineKeyboardButton("😂 نكتة عشوائية", callback_data='joke')],
            [InlineKeyboardButton("🤓 نكتة برمجة", callback_data='joke_prog')],
            [InlineKeyboardButton("🚪 Knock Knock", callback_data='joke_knock')],
            [InlineKeyboardButton("❓ المساعدة", callback_data='help')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = f"""
🎮 *مرحباً بك في بوت 1XBET Crash + النكات!* 🎮

ℹ️ *معرف الحساب:* `{self.dm.api_account}`

هذا البوت يوفر لك:
✅ معلومات الرهانات الحية والمحدثة
✅ إحصائيات تفصيلية ومتقدمة
✅ 😂 نكات عشوائية من API خارجي
✅ 🤓 نكات برمجة متخصصة
✅ 🚪 نكات Knock Knock فكاهية
✅ واجهة سهلة وسريعة

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
        """عرض الإحصائيات"""
        try:
            stats = self.dm.calculate_stats()
            
            if not stats:
                await update.message.reply_text("❌ لا توجد بيانات كافية")
                return
            
            message = f"""
📈 *الإحصائيات:*
━━━━━━━━━━━━━━━━━━━━━━━
📊 عدد الرهانات: `{stats['total_bets']}`
👥 متوسط اللاعبين: `{stats['avg_players']:.0f}`
🔝 أقصى عدد: `{stats['max_players']}`
📉 أقل عدد: `{stats['min_players']}`
━━━━━━━━━━━━━━━━━━━━━━━
📈 أعلى مضاعف: `{stats['max_multiplier']:.2f}`
📉 أقل مضاعف: `{stats['min_multiplier']:.2f}`
📊 متوسط المضاعف: `{stats['avg_multiplier']:.2f}`
━━━━━━━━━━━━━━━━━━━━━━━
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"خطأ في statistics: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def best_performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """أفضل أداء"""
        try:
            if not self.dm.cache:
                await update.message.reply_text("❌ لا توجد بيانات")
                return
            
            best = max(self.dm.cache, key=lambda x: float(x.get('Multiplier(Crash)', 0)))
            
            message = f"""
🏆 *أفضل أداء:*
━━━━━━━━━━━━━━━━━━━━━━━
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
    
    async def random_joke(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """عرض نكتة عشوائية"""
        try:
            loading_msg = await update.message.reply_text("⏳ جاري جلب نكتة عشوائية...")
            
            joke = await self.jm.get_random_joke()
            
            if joke:
                message = self.jm.format_joke(joke)
                await loading_msg.edit_text(message, parse_mode='Markdown')
            else:
                await loading_msg.edit_text("❌ فشل جلب النكتة. حاول لاحقاً")
        except Exception as e:
            logger.error(f"خطأ في random_joke: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def programming_joke(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """عرض نكتة برمجة"""
        try:
            loading_msg = await update.message.reply_text("⏳ جاري جلب نكتة برمجة...")
            
            joke = await self.jm.get_programming_joke()
            
            if joke:
                message = self.jm.format_joke(joke)
                await loading_msg.edit_text(message, parse_mode='Markdown')
            else:
                await loading_msg.edit_text("❌ فشل جلب نكتة البرمجة. حاول لاحقاً")
        except Exception as e:
            logger.error(f"خطأ في programming_joke: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def knock_knock_joke(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """عرض نكتة Knock Knock"""
        try:
            loading_msg = await update.message.reply_text("⏳ جاري جلب نكتة Knock Knock...")
            
            joke = await self.jm.get_knock_knock_joke()
            
            if joke:
                message = self.jm.format_joke(joke)
                await loading_msg.edit_text(message, parse_mode='Markdown')
            else:
                await loading_msg.edit_text("❌ فشل جلب Knock Knock. حاول لاحقاً")
        except Exception as e:
            logger.error(f"خطأ في knock_knock_joke: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """عرض المساعدة"""
        help_text = f"""
🆘 *المساعدة:*
━━━━━━━━━━━━━━━━━━━━━━━

*أوامر الرهانات:*
/latest - آخر رهان 📊
/stats - الإحصائيات 📈
/best - أفضل أداء 🏆

*أوامر النكات:*
/joke - نكتة عشوائية 😂
/joke_prog - نكتة برمجة 🤓
/joke_knock - Knock Knock 🚪
/jokes_list - قائمة النكات 📋

*الميزات:*
✅ نكات من API خارجي موثوق
✅ أنواع متعددة من النكات
✅ دعم العربية كاملاً
✅ سرعة عالية في الاستجابة

━━━━━━━━━━━━━━━━━━━━━━━
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def jokes_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """عرض قائمة النكات المحفوظة"""
        try:
            cached = self.jm.get_cached_jokes()
            
            if not cached:
                await update.message.reply_text("❌ لا توجد نكات محفوظة حالياً")
                return
            
            message = f"""
📋 *قائمة النكات المحفوظة:*
━━━━━━━━━━━━━━━━━━━━━━━
📊 إجمالي النكات المحفوظة: `{len(cached)}`
📈 إجمالي النكات المجلوبة: `{self.jm.total_jokes_fetched}`

*آخر 5 نكات:*
━━━━━━━━━━━━━━━━━━━━━━━
            """
            
            for i, joke in enumerate(cached[-5:], 1):
                setup = joke.get('setup', '')[:50]
                message += f"{i}. {setup}...\n"
            
            message += "━━━━━━━━━━━━━━━━━━━━━━━"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"خطأ في jokes_list: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج الأزرار"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        
        if callback_data == 'latest':
            await self.latest_bet(query, context)
        elif callback_data == 'stats':
            await self.statistics(query, context)
        elif callback_data == 'best':
            await self.best_performance(query, context)
        elif callback_data == 'joke':
            await self.random_joke(query, context)
        elif callback_data == 'joke_prog':
            await self.programming_joke(query, context)
        elif callback_data == 'joke_knock':
            await self.knock_knock_joke(query, context)
        elif callback_data == 'help':
            await self.help_command(query, context)

# ============================================
# 🚀 بدء التطبيق
# ============================================

async def main():
    """بدء البوت المتطور مع النكات"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ لم يتم تعيين TELEGRAM_BOT_TOKEN!")
        return
    
    # إنشاء مدير البيانات والنكات
    data_manager = DataManager(CSV_FILE_PATH)
    joke_manager = JokeManager()
    bot_handlers = BotHandlers(data_manager, joke_manager)
    
    # إنشاء التطبيق
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", bot_handlers.start))
    application.add_handler(CommandHandler("latest", bot_handlers.latest_bet))
    application.add_handler(CommandHandler("stats", bot_handlers.statistics))
    application.add_handler(CommandHandler("best", bot_handlers.best_performance))
    application.add_handler(CommandHandler("joke", bot_handlers.random_joke))
    application.add_handler(CommandHandler("joke_prog", bot_handlers.programming_joke))
    application.add_handler(CommandHandler("joke_knock", bot_handlers.knock_knock_joke))
    application.add_handler(CommandHandler("jokes_list", bot_handlers.jokes_list))
    application.add_handler(CommandHandler("help", bot_handlers.help_command))
    
    # معالج الأزرار
    application.add_handler(CallbackQueryHandler(bot_handlers.button_callback))
    
    logger.info("=" * 70)
    logger.info("🚀 بوت 1XBET Crash + مولد النكات يعمل الآن!")
    logger.info("=" * 70)
    logger.info(f"🔐 معرف الحساب: {API_ACCOUNT}")
    logger.info(f"😂 API النكات: {JOKE_API_URL}")
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
