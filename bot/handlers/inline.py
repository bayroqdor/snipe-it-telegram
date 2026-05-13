import html
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes
from services.snipe_it import snipe_client
from utils.logger import logger

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi qidiruvi uchun inline query handler."""
    query = update.inline_query.query

    # Admin tekshiruvi
    from utils.config import Config
    if Config.ADMIN_IDS and update.effective_user.id not in Config.ADMIN_IDS:
        await update.inline_query.answer([])
        return

    if not query:
        return

    try:
        # Snipe-IT orqali foydalanuvchilarni qidirish
        users = await snipe_client.search_users(query)
        
        results = []
        for user in users:
            user_id = user.get("id")
            name = user.get("name", "Noma'lum")
            username = user.get("username", "")
            employee_num = user.get("employee_num", "")
            
            description = f"Username: {username}"
            if employee_num:
                description += f" | ID: {employee_num}"

            # Natija bosilganda botga xabar qilib yuboriladigan matn
            # Biz uni command ko'rinishida yuboramiz. Shunda MessageHandler uni oson ushlab oladi.
            message_content = InputTextMessageContent(
                message_text=f"/report {user_id}",
                parse_mode="HTML"
            )

            # Inline natijani shakllantirish
            results.append(
                InlineQueryResultArticle(
                    id=str(user_id),
                    title=html.escape(name),
                    description=html.escape(description),
                    input_message_content=message_content,
                    thumbnail_url="https://ui-avatars.com/api/?name=" + name.replace(" ", "+") # Ixtiyoriy avatar
                )
            )

        # Natijalarni foydalanuvchiga qaytarish
        await update.inline_query.answer(results, cache_time=10)
        
    except Exception as e:
        logger.error(f"Inline qidiruvda xatolik: {str(e)}")
        # Xatolik bo'lganda bo'sh natija qaytaramiz (qotib qolmasligi uchun)
        await update.inline_query.answer([])
