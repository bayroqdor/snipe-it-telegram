#!/bin/bash
set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="snipe-it-bot.service"

# Logging Functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

main() {
    log_info "Snipe-IT Bot yangilash jarayoni boshlanmoqda..."

    # Ildiz (root) huquqini tekshirish (systemctl restart uchun kerak)
    if [ "$EUID" -ne 0 ]; then
        log_error "Iltimos, skriptni root (sudo) huquqida ishga tushiring: sudo ./update.sh"
        exit 1
    fi

    cd "$SCRIPT_DIR"

    # Git o'rnatilganligini tekshirish
    if ! command -v git &> /dev/null; then
        log_error "Git o'rnatilmagan! Iltimos 'apt install git' orqali o'rnating."
        exit 1
    fi

    log_info "GitHub dan oxirgi o'zgarishlar yuklab olinmoqda..."
    # Lokal o'zgarishlarni bekor qilib (masalan serverda fayllar o'zgargan bo'lsa qotib qolmasligi uchun)
    # Asosiy tarmoqdan (branchdan) barcha o'zgarishlarni majburiy oladi.
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD || echo "main")
    
    # Ruxsat muammolarini oldini olish uchun
    git config --global --add safe.directory "$SCRIPT_DIR"
    
    git fetch origin "$CURRENT_BRANCH"
    git reset --hard "origin/$CURRENT_BRANCH"

    log_info "Python paketlari yangilanmoqda..."
    if [ -d "venv" ]; then
        # venv papkasiga to'g'ri ruxsatlarni berish
        USER=$(stat -c '%U' "$SCRIPT_DIR/main.py")
        chown -R $USER:$USER "$SCRIPT_DIR/venv" || true
        
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
    else
        log_warn "venv papkasi topilmadi! Dastlab ./deploy.sh orqali o'rnatish qilinganligiga ishonch hosil qiling."
        exit 1
    fi

    log_info "Systemd xizmati qayta ishga tushirilmoqda ($SERVICE_NAME)..."
    systemctl restart "$SERVICE_NAME"

    log_info "Bot muvaffaqiyatli yangilandi va ishga tushdi!"
    log_info "Jarayon loglarini ko'rish uchun: sudo journalctl -u $SERVICE_NAME -f"
}

main "$@"
