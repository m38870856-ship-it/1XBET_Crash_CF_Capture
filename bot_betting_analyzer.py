#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎮 بوت تحليل المراهنات المتقدم - Advanced Betting Analysis Bot
📊 تحليل شامل وتنبؤات ذكية للمراهنات

🔐 API Details:
Token: 8737348077:AAFF_nGiNQGlXerj5dCzWvcoyHsFlppR85I
Account: AAEcsa25t4r0BjKb3koW67OmLBQ_22xVloA:8610233048

Author: m38870856-ship-it
"""

import os
import csv
import json
import asyncio
import logging
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from statistics import mean, median, stdev
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# ============================================
# ⚙️ الإعدادات الرئيسية
# ============================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# معرفات البوت الجديد
TELEGRAM_BOT_TOKEN = "8737348077:AAFF_nGiNQGlXerj5dCzWvcoyHsFlppR85I"
CSV_FILE_PATH = '1XBetCrash.csv'
ANALYTICS_FILE = 'betting_analytics.json'
API_ACCOUNT = "AAEcsa25t4r0BjKb3koW67OmLBQ_22xVloA:8610233048"
BOT_ID = "8737348077"
JOKE_API_URL = "https://official-joke-api.appspot.com/random_joke"

# ============================================
# 📊 فئة تحليل المراهنات
# ============================================

@dataclass
class BettingStats:
    """إحصائيات المراهنات الشاملة"""
    total_bets: int
    avg_multiplier: float
    max_multiplier: float
    min_multiplier: float
    median_multiplier: float
    std_dev: float
    total_players: int
    avg_players: int
    winning_rate: float
    high_crash_rate: float
    crash_count: int
    safe_range: Tuple[float, float]
    risky_range: Tuple[float, float]

@dataclass
class BettingPrediction:
    """تنبؤ ذكي للرهان القادم"""
    likely_range: Tuple[float, float]
    confidence: float
    recommendation: str
    risk_level: str
    description: str

# ============================================
# 🎲 محلل المراهنات المتقدم
# ============================================

class BettingAnalyzer:
    """محلل المراهنات مع ميزات تنبؤ متقدمة"""
    
    def __init__(self, csv_path: str = CSV_FILE_PATH):
        self.csv_path = csv_path
        self.analytics_file = ANALYTICS_FILE
        self.bets = []
        self.last_update = None
        self.api_account = API_ACCOUNT
        self.bot_id = BOT_ID
        self.load_bets()
    
    def load_bets(self) -> List[Dict]:
        """تحميل بيانات الرهانات من CSV"""
        try:
            if not os.path.exists(self.csv_path):
                logger.warning(f"ملف {self.csv_path} غير موجود")
                return []
            
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                self.bets = list(reader)
                self.last_update = datetime.now()
                logger.info(f"✅ تم تحميل {len(self.bets)} رهان من البيانات")
                return self.bets
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل البيانات: {e}")
            return []
    
    def get_multipliers(self) -> List[float]:
        """الحصول على قائمة المضاعفات"""
        multipliers = []
        for bet in self.bets:
            try:
                mult = float(bet.get('Multiplier(Crash)', 0))
                if mult > 0:
                    multipliers.append(mult)
            except (ValueError, TypeError):
                continue
        return multipliers
    
    def get_players_count(self) -> List[int]:
        """الحصول على عدد اللاعبين"""
        players = []
        for bet in self.bets:
            try:
                p = int(bet.get('Number of players', 0))
                if p > 0:
                    players.append(p)
            except (ValueError, TypeError):
                continue
        return players
    
    def calculate_stats(self) -> Optional[BettingStats]:
        """حساب الإحصائيات الشاملة والمتقدمة"""
        try:
            if not self.bets:
                return None
            
            multipliers = self.get_multipliers()
            players = self.get_players_count()
            
            if not multipliers:
                return None
            
            # حساب الإحصائيات الأساسية
            total_bets = len(self.bets)
            avg_mult = mean(multipliers)
            max_mult = max(multipliers)
            min_mult = min(multipliers)
            median_mult = median(multipliers)
            
            # الانحراف المعياري
            std_dev = stdev(multipliers) if len(multipliers) > 1 else 0
            
            # عدد اللاعبين
            total_players = sum(players) if players else 0
            avg_players = mean(players) if players else 0
            
            # معدل الفوز (المضاعفات >= 1.5)
            winning_count = sum(1 for m in multipliers if m >= 1.5)
            winning_rate = (winning_count / len(multipliers)) * 100 if multipliers else 0
            
            # معدل المضاعفات العالية >= 3
            high_crash = sum(1 for m in multipliers if m >= 3)
            high_crash_rate = (high_crash / len(multipliers)) * 100 if multipliers else 0
            
            # عدد الكراشات < 1.5
            crash_count = sum(1 for m in multipliers if m < 1.5)
            
            # المناطق الآمنة والخطرة
            safe_range = (min_mult, avg_mult - std_dev)
            risky_range = (avg_mult + std_dev, max_mult)
            
            return BettingStats(
                total_bets=total_bets,
                avg_multiplier=avg_mult,
                max_multiplier=max_mult,
                min_multiplier=min_mult,
                median_multiplier=median_mult,
                std_dev=std_dev,
                total_players=total_players,
                avg_players=int(avg_players),
                winning_rate=winning_rate,
                high_crash_rate=high_crash_rate,
                crash_count=crash_count,
                safe_range=safe_range,
                risky_range=risky_range
            )
        except Exception as e:
            logger.error(f"❌ خطأ في حساب الإحصائيات: {e}")
            return None
    
    def get_prediction(self) -> Optional[BettingPrediction]:
        """تنبؤ ذكي بالرهان القادم"""
        try:
            stats = self.calculate_stats()
            if not stats:
                return None
            
            avg = stats.avg_multiplier
            std = stats.std_dev
            safe_min = max(1.0, avg - std)
            safe_max = avg + (std * 0.5)
            risky_max = avg + (std * 1.5)
            
            # حساب مستوى الثقة
            confidence = min(95, (stats.winning_rate / 100) * 100) if stats.winning_rate > 0 else 50
            
            # التوصية بناءً على معدل الفوز
            if stats.winning_rate >= 70:
                recommendation = "✅ توصية إيجابية قوية - معدل فوز عالي جداً"
                risk = "🟢 منخفض جداً"
            elif stats.winning_rate >= 60:
                recommendation = "✅ توصية إيجابية - معدل فوز جيد"
                risk = "🟢 منخفض"
            elif stats.winning_rate >= 50:
                recommendation = "⚠️ توصية متوسطة - كن حذراً"
                risk = "🟡 متوسط"
            elif stats.winning_rate >= 40:
                recommendation = "⚠️ توصية سلبية - احذر"
                risk = "🔴 عالي"
            else:
                recommendation = "❌ توصية سلبية جداً - لا تراهن"
                risk = "🔴 عالي جداً"
            
            description = f"""
🎯 النطاق الآمن: `{safe_min:.2f}x - {safe_max:.2f}x`
⚠️ النطاق الخطر: `{risky_max:.2f}x+`
📊 معدل الفوز: `{stats.winning_rate:.1f}%`
🚀 معدل المضاعفات العالية: `{stats.high_crash_rate:.1f}%`
💥 عدد الكراشات: `{stats.crash_count}`
            """
            
            return BettingPrediction(
                likely_range=(safe_min, safe_max),
                confidence=confidence,
                recommendation=recommendation,
                risk_level=risk,
                description=description
            )
        except Exception as e:
            logger.error(f"❌ خطأ في التنبؤ: {e}")
            return None
    
    def get_trend_analysis(self) -> Dict:
        """تحليل الاتجاهات والأنماط"""
        try:
            if len(self.bets) < 10:
                return {"status": "⚠️ بيانات ناقصة - نحتاج 10+ رهانات"}
            
            multipliers = self.get_multipliers()
            recent_10 = multipliers[-10:]
            recent_5 = multipliers[-5:]
            
            avg_recent_10 = mean(recent_10)
            avg_recent_5 = mean(recent_5)
            avg_all = mean(multipliers)
            
            if avg_recent_5 > avg_recent_10:
                trend = "📈 صاعد - معدل المضاعفات يتحسن!"
            elif avg_recent_5 < avg_recent_10:
                trend = "📉 هابط - معدل المضاعفات ينخفض"
            else:
                trend = "➡️ مستقر - بدون تغيير ملحوظ"
            
            return {
                "trend": trend,
                "avg_recent_5": avg_recent_5,
                "avg_recent_10": avg_recent_10,
                "avg_all": avg_all,
                "comparison": f"{avg_recent_5:.2f}x vs {avg_recent_10:.2f}x"
            }
        except Exception as e:
            logger.error(f"❌ خطأ في تحليل الاتجاهات: {e}")
            return {"error": str(e)}
    
    def get_latest_bets(self, limit: int = 5) -> List[Dict]:
        """الحصول على آخر N رهان"""
        return self.bets[-limit:] if self.bets else []
    
    def export_analytics(self) -> bool:
        """تصدير التحليلات الكاملة إلى JSON"""
        try:
            stats = self.calculate_stats()
            prediction = self.get_prediction()
            trend = self.get_trend_analysis()
            
            analytics_data = {
                'exported_at': datetime.now().isoformat(),
                'account': self.api_account,
                'bot_id': self.bot_id,
                'statistics': {
                    'total_bets': stats.total_bets if stats else 0,
                    'avg_multiplier': round(stats.avg_multiplier, 2) if stats else 0,
                    'max_multiplier': round(stats.max_multiplier, 2) if stats else 0,
                    'winning_rate': round(stats.winning_rate, 1) if stats else 0,
                    'crash_count': stats.crash_count if stats else 0,
                } if stats else {},
                'prediction': {
                    'likely_range': [round(prediction.likely_range[0], 2), round(prediction.likely_range[1], 2)] if prediction else None,
                    'confidence': round(prediction.confidence, 1) if prediction else 0,
                    'recommendation': prediction.recommendation if prediction else None,
                    'risk_level': prediction.risk_level if prediction else None,
                } if prediction else {},
                'trend': trend,
                'latest_bets': self.get_latest_bets(10)
            }
            
            with open(self.analytics_file, 'w', encoding='utf-8') as f:
                json.dump(analytics_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ تم تصدير التحليلات إلى {self.analytics_file}")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في تصدير التحليلات: {e}")
            return False

# ============================================
# 😂 مدير النكات
# ============================================

class JokeManager:
    """مدير النكات والترفيه"""
    
    def __init__(self):
        self.joke_cache = []
        self.total_jokes_fetched = 0
    
    async def get_random_joke(self) -> Optional[Dict]:
        """الحصول على نكتة عشوائية من API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(JOKE_API_URL, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        joke = await response.json()
                        self.total_jokes_fetched += 1
                        self.joke_cache.append(joke)
                        if len(self.joke_cache) > 50:
                            self.joke_cache.pop(0)
                        logger.info(f"✅ تم جلب نكتة جديدة")
                        return joke
                    return None
        except Exception as e:
            logger.error(f"❌ خطأ في جلب النكتة: {e}")
            return None
    
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
# 🤖 معالجات البوت المتقدمة
# ============================================

class AdvancedBotHandlers:
    """معالجات البوت المتقدمة مع تحليل شامل"""
    
    def __init__(self, analyzer: BettingAnalyzer, joke_manager: JokeManager):
        self.analyzer = analyzer
        self.joke_manager = joke_manager
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج البدء مع القائمة الرئيسية"""
        keyboard = [
            [InlineKeyboardButton("📊 الإحصائيات", callback_data='stats')],
            [InlineKeyboardButton("🔮 التنبؤ", callback_data='prediction')],
            [InlineKeyboardButton("📈 تحليل الاتجاهات", callback_data='trend')],
            [InlineKeyboardButton("🏆 آخر الرهانات", callback_data='latest')],
            [InlineKeyboardButton("😂 نكتة عشوائية", callback_data='joke')],
            [InlineKeyboardButton("❓ المساعدة", callback_data='help')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome = f"""
╔═══════════════════════════════════════════════╗
║                                               ║
║  🎮 بوت تحليل المراهنات المتقدم 🎮         ║
║                                               ║
║  🔐 معرف البوت: `{self.analyzer.bot_id}`   ║
║  👤 المعرف: `{self.analyzer.api_account}` ║
║                                               ║
╚═══════════════════════════════════════════════╝

📊 *المميزات المتقدمة:*

✅ تحليل شامل ودقيق للمراهنات
✅ تنبؤات ذكية بناءً على البيانات التاريخية
✅ تحليل الاتجاهات والأنماط
✅ إحصائيات متقدمة وتفصيلية
✅ معدلات فوز وخسارة دقيقة
✅ تقييم مستويات المخاطرة
✅ توصيات موثوقة للمراهنات
✅ نكات عشوائية للترفيه 😂

🎯 اختر من الخيارات أدناه:
        """
        
        await update.message.reply_text(welcome, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """عرض الإحصائيات الشاملة والدقيقة"""
        try:
            stats = self.analyzer.calculate_stats()
            
            if not stats:
                await update.message.reply_text("❌ لا توجد بيانات كافية للتحليل")
                return
            
            message = f"""
📊 *الإحصائيات الشاملة:*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 عدد الرهانات: `{stats.total_bets}`
👥 إجمالي اللاعبين: `{stats.total_players:,}`
👤 متوسط اللاعبين: `{stats.avg_players}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 *تحليل المضاعفات:*
🔹 المتوسط: `{stats.avg_multiplier:.2f}x`
🔹 الأعلى: `{stats.max_multiplier:.2f}x` 🚀
🔹 الأقل: `{stats.min_multiplier:.2f}x`
🔹 الوسيط: `{stats.median_multiplier:.2f}x`
🔹 الانحراف المعياري: `{stats.std_dev:.2f}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 *معدلات النجاح والفشل:*
✅ معدل الفوز: `{stats.winning_rate:.1f}%`
🚀 معدل المضاعفات العالية (3+): `{stats.high_crash_rate:.1f}%`
💥 عدد الكراشات: `{stats.crash_count}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 المنطقة الآمنة: `{stats.safe_range[0]:.2f} - {stats.safe_range[1]:.2f}x`
🔴 المنطقة الخطرة: `{stats.risky_range[0]:.2f} - {stats.risky_range[1]:.2f}x`
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def show_prediction(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """عرض التنبؤ الذكي للرهان القادم"""
        try:
            prediction = self.analyzer.get_prediction()
            
            if not prediction:
                await update.message.reply_text("❌ لا يمكن إنشاء تنبؤ حالياً")
                return
            
            message = f"""
🔮 *التنبؤ الذكي للرهان القادم:*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{prediction.recommendation}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 *النطاق المتوقع:*
   من: `{prediction.likely_range[0]:.2f}x`
   إلى: `{prediction.likely_range[1]:.2f}x`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 مستوى الثقة: `{prediction.confidence:.0f}%`
⚠️ مستوى المخاطرة: {prediction.risk_level}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{prediction.description}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def show_trend(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """عرض تحليل الاتجاهات والأنماط"""
        try:
            trend = self.analyzer.get_trend_analysis()
            
            message = f"""
📈 *تحليل الاتجاهات:*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 الاتجاه الحالي: {trend.get('trend', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 *المقارنة والتحليل:*
🔹 آخر 5 رهانات: `{trend.get('avg_recent_5', 0):.2f}x`
🔹 آخر 10 رهانات: `{trend.get('avg_recent_10', 0):.2f}x`
🔹 المتوسط العام: `{trend.get('avg_all', 0):.2f}x`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 التحليل: {trend.get('comparison', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def show_latest_bets(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """عرض آخر الرهانات مع التفاصيل"""
        try:
            latest = self.analyzer.get_latest_bets(5)
            
            if not latest:
                await update.message.reply_text("❌ لا توجد رهانات")
                return
            
            message = "🏆 *آخر 5 رهانات:*\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            for i, bet in enumerate(latest, 1):
                time = bet.get('Time', 'N/A')
                players = bet.get('Number of players', 'N/A')
                mult = bet.get('Multiplier(Crash)', 'N/A')
                gains = bet.get('Total gains', 'N/A')
                total_bets = bet.get('Total bets', 'N/A')
                
                message += f"""
{i}. ⏰ الوقت: {time}
   👥 اللاعبين: {players}
   💰 الرهانات: {total_bets}
   📈 المضاعف: `{mult}x`
   🎯 الأرباح: {gains}
━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def show_joke(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """عرض نكتة عشوائية للترفيه"""
        try:
            loading = await update.message.reply_text("⏳ جاري جلب نكتة مرحة...")
            joke = await self.joke_manager.get_random_joke()
            
            if joke:
                message = self.joke_manager.format_joke(joke)
                await loading.edit_text(message, parse_mode='Markdown')
            else:
                await loading.edit_text("❌ فشل جلب النكتة. حاول لاحقاً")
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
    
    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """عرض المساعدة والأوامر"""
        help_text = f"""
❓ *المساعدة والأوامر:*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 *معرفات البوت:*
🔐 Token: `{self.analyzer.bot_id}`
👤 Account: `{self.analyzer.api_account}`

*الأوامر المتاحة:*
/start - القائمة الرئيسية 🎮
/stats - الإحصائيات الشاملة 📊
/prediction - التنبؤ الذكي 🔮
/trend - تحليل الاتجاهات 📈
/latest - آخر الرهانات 🏆
/joke - نكتة عشوائية 😂
/help - هذه الرسالة ❓

*المميزات الرئيسية:*
✅ تحليل دقيق للبيانات التاريخية
✅ تنبؤات ذكية بناءً على الإحصائيات
✅ تقييم مستويات المخاطرة
✅ توصيات موثوقة للمراهنات
✅ تحديث فوري للبيانات
✅ دعم كامل للعربية

*نصائح مهمة:*
💡 ادرس الإحصائيات بعناية
💡 انتبه لمستوى الثقة
💡 احترم مستويات المخاطرة
💡 لا تراهن أكثر من احتمالك

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج الأزرار التفاعلية"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'stats':
            await self.show_statistics(query, context)
        elif query.data == 'prediction':
            await self.show_prediction(query, context)
        elif query.data == 'trend':
            await self.show_trend(query, context)
        elif query.data == 'latest':
            await self.show_latest_bets(query, context)
        elif query.data == 'joke':
            await self.show_joke(query, context)
        elif query.data == 'help':
            await self.show_help(query, context)

# ============================================
# 🚀 بدء التطبيق
# ============================================

async def main():
    """بدء البوت المتقدم مع كل المميزات"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ لم يتم تعيين TELEGRAM_BOT_TOKEN!")
        return
    
    # إنشاء المديرين
    analyzer = BettingAnalyzer(CSV_FILE_PATH)
    joke_manager = JokeManager()
    handlers = AdvancedBotHandlers(analyzer, joke_manager)
    
    # إنشاء التطبيق
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("stats", handlers.show_statistics))
    application.add_handler(CommandHandler("prediction", handlers.show_prediction))
    application.add_handler(CommandHandler("trend", handlers.show_trend))
    application.add_handler(CommandHandler("latest", handlers.show_latest_bets))
    application.add_handler(CommandHandler("joke", handlers.show_joke))
    application.add_handler(CommandHandler("help", handlers.show_help))
    application.add_handler(CallbackQueryHandler(handlers.button_handler))
    
    logger.info("=" * 70)
    logger.info("🚀 بوت تحليل المراهنات المتقدم يعمل الآن!")
    logger.info("=" * 70)
    logger.info(f"🔐 معرف البوت: {analyzer.bot_id}")
    logger.info(f"👤 المعرف: {analyzer.api_account}")
    logger.info(f"📊 عدد الرهانات: {len(analyzer.bets)}")
    logger.info("=" * 70)
    
    # تصدير التحليلات الأولية
    analyzer.export_analytics()
    
    # بدء البوت
    await application.run_polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 تم إيقاف البوت بنجاح")
    except Exception as e:
        logger.error(f"❌ خطأ في البوت: {e}")
