#!/bin/bash
# Snipe-IT Telegram Bot Ubuntu Deployment Script
# Ushbu skript botni Ubuntu serveriga avtomatlashtirilgan tarzda o'rnatadi.

set -e

# Ildiz (root) huquqini tekshirish
if [ "$EUID" -ne 0 ]; then
  echo "Iltimos, skriptni root (sudo) huquqida ishga tushiring."
  echo "Masalan: sudo ./deploy.sh"
  exit 1
fi

APP_DIR=$(pwd)
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="snipe-it-bot.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
USER=$(logname || echo $SUDO_USER)

echo "============================================"
echo " Snipe-IT Bot O'rnatish Dasturi "
echo "============================================"
echo "O'rnatish papkasi: $APP_DIR"
echo "Foydalanuvchi: $USER"
echo ""

echo "[1/6] Tizim paketlari yangilanmoqda..."
apt update
apt install -y python3 python3-venv python3-pip curl unzip

echo "[2/6] Deno o'rnatilmoqda..."
# Agar deno buyrug'i mavjud bo'lmasa o'rnatamiz
if ! command -v deno &> /dev/null; then
    # Foydalanuvchi uchun Deno ni o'rnatish
    su - $USER -c "curl -fsSL https://deno.land/install.sh | sh -s -- -y"
    
    # Deno ni global path ga qo'shish (hamma userlar uchun)
    export DENO_INSTALL="/home/$USER/.deno"
    ln -sf $DENO_INSTALL/bin/deno /usr/local/bin/deno
    echo "Deno muvaffaqiyatli o'rnatildi."
else
    echo "Deno allaqachon o'rnatilgan."
fi

echo "[3/6] Python virtual muhiti sozlanmoqda..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

# Install requirements
source "$VENV_DIR/bin/activate" && pip install --upgrade pip && pip install -r "$APP_DIR/requirements.txt"

# Chown APP_DIR to USER so the bot service can access it
chown -R $USER:$USER "$APP_DIR"

echo "[4/6] .env faylini tekshirish..."
if [ ! -f "$APP_DIR/.env" ]; then
    if [ -f "$APP_DIR/.env.example" ]; then
        cp "$APP_DIR/.env.example" "$APP_DIR/.env"
        chown $USER:$USER "$APP_DIR/.env"
        echo "DIQQAT: .env fayli yaratildi. Iltimos, o'rnatish tugagach, tokenlarni kiriting!"
    else
        echo "Ogohlantirish: .env fayli va .env.example fayli topilmadi!"
    fi
else
    echo ".env fayli mavjud."
fi

echo "[5/6] Systemd service yaratilmoqda..."
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Snipe-IT Telegram Bot
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin:/usr/local/bin:/usr/bin:/home/$USER/.deno/bin"
Environment="PYTHONPATH=$APP_DIR"
ExecStart=$APP_DIR/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

echo "[6/6] Bot ishga tushirilmoqda..."
systemctl enable $SERVICE_NAME
systemctl restart $SERVICE_NAME

echo "============================================"
echo " O'rnatish muvaffaqiyatli yakunlandi! "
echo "============================================"
echo "Bot holatini tekshirish uchun: sudo systemctl status $SERVICE_NAME"
echo "Bot loglarini ko'rish uchun: sudo journalctl -u $SERVICE_NAME -f"
echo "Eslatma: Agar .env faylini tahrirlamagan bo'lsangiz, 'nano .env' orqali o'zgartiring va botni qayta ishga tushiring: sudo systemctl restart $SERVICE_NAME"
