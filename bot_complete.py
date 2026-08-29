import os
import csv
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# الحصول على API Token من متغيرات البيئة
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CSV_FILE_PATH = '1XBetCrash.csv'

# ============================================
# 📊 دوال قراءة البيانات
# ============================================

def read_csv_data():
    """قراءة بيانات CSV"""
    try:
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return list(reader)
    except FileNotFoundError:
        logger.error(f"ملف {CSV_FILE_PATH} غير موجود")
        return []

def get_latest_bet():
    """الحصول على آخر رهان"""
    rows = read_csv_data()
    if rows:
        return rows[-1]
    return None

def get_all_bets():
    """الحصول على جميع الرهانات"""
    return read_csv_data()

def calculate_stats():
    """حساب الإحصائيات"""
    rows = read_csv_data()
    
    if not rows:
        return None
    
    try:
        # تحويل البيانات
        players_list = [int(row.get('Number of players', 0)) for row in rows if row.get('Number of players')]
        multipliers = [float(row.get('Multiplier(Crash)', 0)) for row in rows if row.get('Multiplier(Crash)')]
        
        stats = {
            'total_bets': len(rows),
            'avg_players': sum(players_list) / len(players_list) if players_list else 0,
            'max_players': max(players_list) if players_list else 0,
            'min_players': min(players_list) if players_list else 0,
            'max_multiplier': max(multipliers) if multipliers else 0,
            'min_multiplier': min(multipliers) if multipliers else 0,
            'avg_multiplier': sum(multipliers) / len(multipliers) if multipliers else 0,
        }
        return stats
    except Exception as e:
        logger.error(f"خطأ في حساب الإحصائيات: {e}")
        return None

# ============================================
# 🤖 معالجات أوامر البوت
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر البدء"""
    keyboard = [
        [InlineKeyboardButton("📊 آخر رهان", callback_data='latest')],
        [InlineKeyboardButton("📈 الإحصائيات", callback_data='stats')],
        [InlineKeyboardButton("📋 جميع البيانات", callback_data='all')],
        [InlineKeyboardButton("🔝 أفضل أداء", callback_data='best')],
        [InlineKeyboardButton("📉 أسوأ أداء", callback_data='worst')],
        [InlineKeyboardButton("❓ المساعدة", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = """
🎮 *مرحباً بك في بوت 1XBET Crash!* 🎮

هذا البوت يوفر لك:
✅ معلومات الرهانات الحية
✅ إحصائيات تفصيلية
✅ تحليل الأداء
✅ بيانات دقيقة من 1XBET

اختر من الخيارات أدناه:
    """
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def latest_bet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض آخر رهان"""
    try:
        latest = get_latest_bet()
        
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

async def statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض الإحصائيات"""
    try:
        stats = calculate_stats()
        
        if not stats:
            await update.message.reply_text("❌ لا توجد بيانات كافية")
            return
        
        message = f"""
📈 *الإحصائيات:*
━━━━━━━━━━━━━━━━━━━━━━━
📊 عدد الرهانات: `{stats['total_bets']}`
👥 متوسط اللاعبين: `{stats['avg_players']:.0f}`
🔝 أقصى عدد لاعبين: `{stats['max_players']}`
📉 أقل عدد لاعبين: `{stats['min_players']}`
📈 أعلى مضاعف: `{stats['max_multiplier']}`
📉 أقل مضاعف: `{stats['min_multiplier']}`
📊 متوسط المضاعف: `{stats['avg_multiplier']:.2f}`
━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"خطأ في statistics: {e}")
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")

async def all_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض جميع البيانات"""
    try:
        bets = get_all_bets()
        
        if not bets:
            await update.message.reply_text("❌ لا توجد بيانات")
            return
        
        if len(bets) > 50:
            await update.message.reply_text(
                f"📊 يوجد {len(bets)} رهان\n\n"
                "البيانات كثيرة جداً! استخدم:\n"
                "/latest - آخر رهان\n"
                "/stats - الإحصائيات\n"
                "/best - أفضل أداء\n"
                "/worst - أسوأ أداء"
            )
            return
        
        # عرض جميع البيانات
        header = "رقم | الوقت | اللاعبين | المضاعف\n"
        header += "─" * 40 + "\n"
        
        data_str = header
        for i, bet in enumerate(bets[-20:], 1):  # عرض آخر 20 رهان
            data_str += f"{i:2d} | {bet.get('Time', 'N/A')} | {bet.get('Number of players', 'N/A')} | {bet.get('Multiplier(Crash)', 'N/A')}\n"
        
        await update.message.reply_text(f"```\n{data_str}\n```", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"خطأ في all_data: {e}")
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")

async def best_performance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أفضل أداء"""
    try:
        bets = get_all_bets()
        
        if not bets:
            await update.message.reply_text("❌ لا توجد بيانات")
            return
        
        # ترتيب حسب المضاعف (الأعلى)
        sorted_bets = sorted(bets, key=lambda x: float(x.get('Multiplier(Crash)', 0)), reverse=True)
        best = sorted_bets[0]
        
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

async def worst_performance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أسوأ أداء"""
    try:
        bets = get_all_bets()
        
        if not bets:
            await update.message.reply_text("❌ لا توجد بيانات")
            return
        
        # ترتيب حسب المضاعف (الأقل)
        sorted_bets = sorted(bets, key=lambda x: float(x.get('Multiplier(Crash)', 0)))
        worst = sorted_bets[0]
        
        message = f"""
📉 *أسوأ أداء:*
━━━━━━━━━━━━━━━━━━━━━━━
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض المساعدة"""
    help_text = """
🆘 *المساعدة:*
━━━━━━━━━━━━━━━━━━━━━━━

*الأوامر المتاحة:*
/start - ابدأ البوت
/latest - آخر رهان 📊
/stats - الإحصائيات 📈
/all - جميع البيانات 📋
/best - أفضل أداء 🏆
/worst - أسوأ أداء 📉
/help - المساعدة ❓

*الميزات:*
✅ جلب البيانات من 1XBetCrash.csv
✅ إحصائيات فورية
✅ تحليل الأداء
✅ بيانات دقيقة وموثوقة
✅ واجهة سهلة الاستخدام

━━━━━━━━━━━━━━━━━━━━━━━
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الأزرار"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data == 'latest':
        await query.edit_message_text(text="جاري جلب البيانات...")
        await latest_bet(query, context)
    elif callback_data == 'stats':
        await query.edit_message_text(text="جاري حساب الإحصائيات...")
        await statistics(query, context)
    elif callback_data == 'all':
        await query.edit_message_text(text="جاري جلب جميع البيانات...")
        await all_data(query, context)
    elif callback_data == 'best':
        await query.edit_message_text(text="جاري البحث عن أفضل أداء...")
        await best_performance(query, context)
    elif callback_data == 'worst':
        await query.edit_message_text(text="جاري البحث عن أسوأ أداء...")
        await worst_performance(query, context)
    elif callback_data == 'help':
        await help_command(query, context)

# ============================================
# 🚀 بدء البوت
# ============================================

def main():
    """بدء البوت"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ لم يتم تعيين TELEGRAM_BOT_TOKEN!")
        logger.error("أضف التوكن في ملف .env")
        return
    
    # إنشاء التطبيق
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("latest", latest_bet))
    application.add_handler(CommandHandler("stats", statistics))
    application.add_handler(CommandHandler("all", all_data))
    application.add_handler(CommandHandler("best", best_performance))
    application.add_handler(CommandHandler("worst", worst_performance))
    application.add_handler(CommandHandler("help", help_command))
    
    # معالج الأزرار
    application.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("=" * 50)
    logger.info("🚀 بوت 1XBET Crash يعمل الآن!")
    logger.info("=" * 50)
    logger.info(f"📁 ملف البيانات: {CSV_FILE_PATH}")
    logger.info("=" * 50)
    
    # بدء البوت
    application.run_polling()

if __name__ == '__main__':
    main()
