import logging
import sys
from utils.config import Config

def setup_logger():
    """Bot va xizmatlar uchun yagona loglash tizimini o'rnatish."""
    
    # Log formatini belgilash
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console uchun handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Root logger sozlamalari
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO))
    
    # Oldingi handlerlarni tozalash (agar mavjud bo'lsa)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(console_handler)

    # Ba'zi tashqi kutubxonalarni loglarini kamaytirish
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)

    return root_logger

# Import qilinganda avtomatik sozlash
logger = setup_logger()
