import io
from telegram import Update
from telegram.ext import ContextTypes
from services.snipe_it import snipe_client
from services.pdf_service import pdf_service
from utils.logger import logger

async def report_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /report <user_id> buyrug'ini ushlab olish va hujjat yuborish.
    Bu buyruq ko'pincha inline natijani tanlagandan keyin botga avtomatik yuboriladi.
    """
    # Admin tekshiruvi
    from utils.config import Config
    if Config.ADMIN_IDS and update.effective_user.id not in Config.ADMIN_IDS:
        return

    # Xabar matnini tekshirish
    message_text = update.message.text
    parts = message_text.split()
    
    if len(parts) < 2 or not parts[1].isdigit():
        await update.message.reply_text("Iltimos, to'g'ri foydalanuvchi ID sini kiriting. Masalan: /report 123")
        return
        
    user_id = int(parts[1])
    
    # Yuklanayotgani haqida xabar
    status_msg = await update.message.reply_text("⏳ Ma'lumotlar Snipe-IT dan yuklanmoqda...")
    
    try:
        # Fayl yuborish indikatori
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='upload_document')
        
        # 1. API dan ma'lumotlarni tortish
        report_data = await snipe_client.get_full_user_report(user_id)
        
        user_info = report_data.get("user", {})
        if not user_info:
            await status_msg.edit_text(f"❌ Xatolik: {user_id} ID ga ega foydalanuvchi topilmadi.")
            return
            
        user_name = user_info.get("name", f"User {user_id}")
        
        # Holatni yangilash
        await status_msg.edit_text("⏳ PDF hisobot generatsiya qilinmoqda...")
        
        # 2. PDF generatsiya qilish
        pdf_bytes = await pdf_service.generate_pdf(user_name, report_data)
        
        # 3. PDF ni yuborish
        # Xotiradagi baytlarni faylga aylantirib jo'natamiz
        document = io.BytesIO(pdf_bytes)
        document.name = f"{user_name}_hisoboti.pdf"
        
        # Aktivlar ro'yxati
        assets_text = ""
        for a in report_data.get("assets", []):
            name = a.get("name") or a.get("model", {}).get("name", "Noma'lum")
            tag = a.get("asset_tag", "")
            assets_text += f"▪️ {name} (ID: {tag})\n"
        if not assets_text:
            assets_text = "▪️ Mavjud emas\n"

        # Tizim ruxsatlari ro'yxati
        licenses_text = ""
        for l in report_data.get("licenses", []):
            name = l.get('name', 'Nomalum')
            notes = l.get('notes', '')
            if notes:
                licenses_text += f"▪️ {name} (Ruxsat: {notes})\n"
            else:
                licenses_text += f"▪️ {name}\n"
        if not licenses_text:
            licenses_text = "▪️ Mavjud emas\n"

        # Telefon raqamlari ro'yxati
        accessories_text = ""
        for acc in report_data.get("accessories", []):
            accessories_text += f"▪️ {acc.get('name', 'Nomalum')}\n"
        if not accessories_text:
            accessories_text = "▪️ Mavjud emas\n"

        caption_text = (
            f"👤 <b>Xodim:</b> {user_name}\n\n"
            f"📦 <b>Aktivlar:</b>\n{assets_text}\n"
            f"🔑 <b>Tizim ruxsatlari:</b>\n{licenses_text}\n"
            f"📱 <b>Telefon raqamlari:</b>\n{accessories_text}"
        )
        
        # Telegram caption uzunligi cheklangan (1024 belgi), shuning uchun qisqartirish
        if len(caption_text) > 1000:
            caption_text = caption_text[:1000] + "...\n<i>(Qolgan ma'lumotlar PDF faylida)</i>"
        
        await update.message.reply_document(
            document=document,
            caption=caption_text,
            parse_mode="HTML"
        )
        
        # Eski holat xabarini o'chirib tashlaymiz
        await status_msg.delete()
        
    except Exception as e:
        logger.error(f"Hisobot yaratishda xatolik yuz berdi (User ID: {user_id}): {str(e)}")
        await status_msg.edit_text("❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring yoki administratorga murojaat qiling.")
