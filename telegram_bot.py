import os
import csv
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر البدء"""
    welcome_message = """
🎮 مرحباً بك في بوت 1XBET Crash! 

الأوامر المتاحة:
/latest - عرض آخر رهان
/stats - عرض الإحصائيات
/all - عرض جميع البيانات
/help - المساعدة
    """
    await update.message.reply_text(welcome_message)

async def get_latest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض آخر رهان"""
    try:
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            if len(lines) > 1:
                last_row = lines[-1].strip()
                parts = last_row.split(',')
                
                message = f"""
📊 آخر رهان:
━━━━━━━━━━━━━━━━━━
⏰ الوقت: {parts[0]}
👥 عدد اللاعبين: {parts[1]}
💰 إجمالي الرهانات: {parts[2]}
📈 المضاعف: {parts[3]}
🎯 الأرباح الكلية: {parts[4]}
━━━━━━━━━━━━━━━━━━
                """
                await update.message.reply_text(message)
            else:
                await update.message.reply_text("❌ لا توجد بيانات متاحة حالياً")
    except Exception as e:
        logger.error(f"خطأ في get_latest: {e}")
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")

async def get_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض الإحصائيات"""
    try:
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            
            if not rows:
                await update.message.reply_text("❌ لا توجد بيانات")
                return
            
            # حساب الإحصائيات
            total_bets = len(rows)
            avg_players = sum(int(row['Number of players']) for row in rows) / total_bets
            max_multiplier = max(float(row['Multiplier(Crash)']) for row in rows)
            min_multiplier = min(float(row['Multiplier(Crash)']) for row in rows)
            
            stats_message = f"""
📈 الإحصائيات:
━━━━━━━━━━━━━━━━━━
📊 عدد الرهانات: {total_bets}
👥 متوسط اللاعبين: {avg_players:.0f}
📈 أعلى مضاعف: {max_multiplier}
📉 أقل مضاعف: {min_multiplier}
━━━━━━━━━━━━━━━━━━
            """
            await update.message.reply_text(stats_message)
    except Exception as e:
        logger.error(f"خطأ في get_stats: {e}")
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")

async def get_all_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض جميع البيانات"""
    try:
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as file:
            content = file.read()
            if len(content) > 4000:
                await update.message.reply_text("البيانات كثيرة جداً. استخدم /latest أو /stats")
            else:
                await update.message.reply_text(f"```\n{content}\n```", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"خطأ في get_all_data: {e}")
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض المساعدة"""
    help_text = """
🆘 المساعدة:

/start - ابدأ هنا
/latest - آخر رهان
/stats - إحصائيات
/all - جميع البيانات
/help - هذه الرسالة

💡 الميزات:
✅ جلب البيانات تلقائياً
✅ إحصائيات فورية
✅ آخر التحديثات
    """
    await update.message.reply_text(help_text)

def main():
    """بدء البوت"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ لم يتم تعيين TELEGRAM_BOT_TOKEN!")
        return
    
    # إنشاء التطبيق
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("latest", get_latest))
    application.add_handler(CommandHandler("stats", get_stats))
    application.add_handler(CommandHandler("all", get_all_data))
    application.add_handler(CommandHandler("help", help_command))
    
    logger.info("🚀 البوت يعمل الآن...")
    
    # بدء البوت
    application.run_polling()

if __name__ == '__main__':
    main()
