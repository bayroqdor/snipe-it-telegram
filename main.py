import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, InlineQueryHandler, MessageHandler, filters
from utils.config import Config
from utils.logger import logger
from bot.handlers.inline import inline_query_handler
from bot.handlers.report import report_command_handler

async def start_handler(update: Update, context):
    """Botga start bosilganda yuboriladigan xabar."""
    if Config.ADMIN_IDS and update.effective_user.id not in Config.ADMIN_IDS:
        # Admin bo'lmagan foydalanuvchilar uchun hech qanday javob qaytarmaymiz
        return

    await update.message.reply_text(
        "👋 Assalomu alaykum! Snipe-IT hisobot botiga xush kelibsiz.\n\n"
        "🔎 Xodimlarni qidirish uchun istalgan chatda bot nomini yozing (masalan: @bot_username ism)\n"
        "Natijani tanlaganingizdan so'ng, men sizga PDF hisobotni jo'nataman."
    )

def main():
    """Botni ishga tushirish uchun asosiy funksiya."""
    logger.info("Bot ishga tushmoqda...")
    
    # Konfiguratsiya tekshiruvi (xatolik bo'lsa dastur to'xtaydi)
    try:
        Config.validate()
    except Exception as e:
        logger.critical(f"Konfiguratsiya xatosi: {e}")
        return

    # Application qurish
    application = ApplicationBuilder().token(Config.TELEGRAM_BOT_TOKEN).build()

    # Handlerlarni ro'yxatga olish
    application.add_handler(CommandHandler("start", start_handler))
    
    # Inline qidiruv uchun handler
    application.add_handler(InlineQueryHandler(inline_query_handler))
    
    # /report command orqali keladigan xabarlarni ushlab olish (Inline query natijasidan)
    application.add_handler(CommandHandler("report", report_command_handler))
    
    # Yoki oddiy matn orqali keladigan buyruqlarni (agar foydalanuvchi to'g'ridan to'g'ri yozsa)
    application.add_handler(MessageHandler(filters.Regex(r"^/report \d+$"), report_command_handler))

    # Pollingni boshlash
    logger.info("Bot tayyor. Polling boshlandi...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
