import os
from dotenv import load_dotenv

# Atrof-muhit o'zgaruvchilarini .env faylidan o'qib olish
load_dotenv()

class Config:
    """Ilova sozlamalari va atrof-muhit o'zgaruvchilarini saqlovchi klass"""
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Snipe-IT
    SNIPE_IT_URL = os.getenv("SNIPE_IT_URL", "").rstrip("/")
    SNIPE_IT_API_TOKEN = os.getenv("SNIPE_IT_API_TOKEN")
    
    # Adminlar
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip().isdigit()]
    
    # Boshqa sozlamalar
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Katalogni aniqlash (Skills papkasi qayerdaligini topish uchun)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    
    @classmethod
    def validate(cls):
        """Muhim o'zgaruvchilar mavjudligini tekshirish"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN topilmadi. Iltimos, .env faylini tekshiring.")
        if not cls.SNIPE_IT_URL or not cls.SNIPE_IT_API_TOKEN:
            raise ValueError("SNIPE_IT_URL yoki SNIPE_IT_API_TOKEN topilmadi. Iltimos, .env faylini tekshiring.")

# Ishga tushishdan oldin validatsiya qilish
try:
    Config.validate()
except ValueError as e:
    import logging
    logging.error(e)
