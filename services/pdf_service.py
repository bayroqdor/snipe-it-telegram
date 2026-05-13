import os
import json
import uuid
import asyncio
from typing import Dict, Any, List
from utils.config import Config
from utils.logger import logger

def cyrillic_to_latin(text: str) -> str:
    """PDF kutubxonasi Kirill harflarini qo'llab-quvvatlamagani uchun ularni Lotinchaga o'giradi."""
    if not text:
        return ""
    mapping = {
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo', 'Ж': 'J',
        'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O',
        'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'X', 'Ц': 'Ts',
        'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sh', 'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu',
        'Я': 'Ya', 'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'j', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
        'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'x',
        'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sh', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e',
        'ю': 'yu', 'я': 'ya', 'ў': "o'", 'Ў': "O'", 'қ': 'q', 'Қ': 'Q', 'ғ': "g'", 'Ғ': "G'",
        'ҳ': 'h', 'Ҳ': 'H'
    }
    return "".join(mapping.get(c, c) for c in text)

class PDFGeneratorService:
    """Ma'lumotlar asosida Deno pdf-generator skill orqali PDF yaratuvchi xizmat."""

    
    def __init__(self):
        # Deno skriptining joylashuvi
        self.script_path = os.path.join(Config.BASE_DIR, "services", "pdf_generator", "generate.ts")
        # Vaqtinchalik fayllar uchun papka
        self.temp_dir = os.path.join(Config.BASE_DIR, "temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        
    def _create_spec(self, user_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """PDF generatsiyasi uchun JSON spetsifikatsiyani yaratish."""
        pages = []
        elements = []
        current_y = 800
        
        def new_page():
            nonlocal pages, elements, current_y
            pages.append({"size": "A4", "elements": elements})
            elements = []
            current_y = 800

        def add_text(text, font_size=12, font="Helvetica", bold=False, gap=20):
            nonlocal elements, current_y
            if current_y - gap < 50:
                new_page()
            
            elements.append({
                "type": "text",
                "x": 50,
                "y": current_y,
                "text": text,
                "fontSize": font_size,
                "font": "HelveticaBold" if bold else font
            })
            current_y -= gap

        # Sarlavha
        latin_user_name = cyrillic_to_latin(user_name)
        add_text(f"Xodim: {latin_user_name}", font_size=20, bold=True, gap=15)
        
        elements.append({
            "type": "line",
            "startX": 50,
            "startY": current_y + 5,
            "endX": 545, # Jami 495 kenglik
            "endY": current_y + 5,
            "thickness": 2
        })
        current_y -= 25

        def estimate_row_height(row, col_widths):
            max_lines = 1
            for text, width in zip(row, col_widths):
                # approximate chars per line assuming 6px per char for 10pt font
                chars_per_line = max(1, int(width / 6))
                # string length division + actual newlines
                text_str = str(text)
                lines = max(1, (len(text_str) // chars_per_line) + 1) + text_str.count('\n')
                if lines > max_lines:
                    max_lines = lines
            return max(20, max_lines * 12 + 10) # 12px per line + 10px padding

        def add_table_section(title, headers, items, row_mapper, col_widths, empty_text):
            nonlocal elements, current_y
            
            add_text(title, font_size=14, bold=True, gap=15)
            
            if not items:
                add_text(empty_text, font_size=12, gap=25)
                return
                
            data_rows = [row_mapper(item) for item in items]
            
            while data_rows:
                if current_y - 40 < 50:
                    new_page()
                
                header_height = estimate_row_height(headers, col_widths)
                available_height = current_y - 50
                
                chunk = []
                row_heights = [header_height]
                used_height = header_height
                
                for row in data_rows:
                    rh = estimate_row_height(row, col_widths)
                    if used_height + rh > available_height and chunk:
                        break # Sahifaga sig'maydi
                    chunk.append(row)
                    row_heights.append(rh)
                    used_height += rh
                
                if not chunk:
                    new_page()
                    continue
                    
                data_rows = data_rows[len(chunk):]
                table_rows = [headers] + chunk
                
                elements.append({
                    "type": "table",
                    "x": 50,
                    "y": current_y,
                    "rows": table_rows,
                    "columnWidths": col_widths,
                    "rowHeights": row_heights,
                    "headerBackground": {"r": 0.9, "g": 0.9, "b": 0.9}
                })
                
                current_y -= used_height + 20
                
                if data_rows:
                    new_page()

        # Aktivlar jadvali
        assets = data.get("assets", [])
        add_table_section(
            title="Aktivlar",
            headers=["ID", "Nomi", "Modeli"],
            items=assets,
            row_mapper=lambda a: [
                cyrillic_to_latin(str(a.get("asset_tag", ""))),
                cyrillic_to_latin(str(a.get("name", ""))),
                cyrillic_to_latin(str(a.get("model", {}).get("name", "")) if isinstance(a.get("model"), dict) else "")
            ],
            col_widths=[100, 200, 195], # Jami 495
            empty_text="Aktivlar mavjud emas."
        )

        # Litsenziyalar (Tizim ruxsatlari)
        licenses = data.get("licenses", [])
        add_table_section(
            title="Tizim ruxsatlari",
            headers=["Nomi", "Ruxsatlar"],
            items=licenses,
            row_mapper=lambda l: [
                cyrillic_to_latin(str(l.get("name") or "")),
                cyrillic_to_latin(str(l.get("notes") or ""))
            ],
            col_widths=[200, 295],
            empty_text="Tizim ruxsatlari mavjud emas."
        )

        # Aksessuarlar (Telefon raqamlari)
        accessories = data.get("accessories", [])
        add_table_section(
            title="Telefon raqamlari",
            headers=["Nomi"],
            items=accessories,
            row_mapper=lambda acc: [cyrillic_to_latin(str(acc.get("name", "")))],
            col_widths=[495],
            empty_text="Telefon raqamlari mavjud emas."
        )

        # So'nggi sahifani qo'shish
        if elements:
            pages.append({
                "size": "A4",
                "elements": elements
            })

        return {
            "title": f"{user_name} Hisoboti",
            "author": "Snipe-IT Telegram Bot",
            "pages": pages
        }

    async def generate_pdf(self, user_name: str, data: Dict[str, Any]) -> bytes:
        """Ma'lumotlarni qabul qilib, PDF fayl baytlarini qaytaradi."""
        
        if not os.path.exists(self.script_path):
            raise FileNotFoundError(f"Deno skripti topilmadi: {self.script_path}")

        spec = self._create_spec(user_name, data)
        file_id = str(uuid.uuid4())
        
        spec_path = os.path.join(self.temp_dir, f"{file_id}_spec.json")
        pdf_path = os.path.join(self.temp_dir, f"{file_id}_report.pdf")
        
        try:
            # 1. Spec faylini saqlash
            with open(spec_path, 'w', encoding='utf-8') as f:
                json.dump(spec, f, ensure_ascii=False, indent=2)
                
            # 2. Deno orqali generatsiya qilish
            # subprocess.exec yordamida buyruqni asinxron ishga tushirish
            # Deno yo'lini topish
            import shutil
            deno_executable = shutil.which("deno")
            if not deno_executable:
                # Agar PATH da bo'lmasa, standart o'rnatish yo'lidan qidirib ko'ramiz
                default_deno = os.path.expanduser("~/.deno/bin/deno.exe")
                if os.path.exists(default_deno):
                    deno_executable = default_deno
                else:
                    raise FileNotFoundError("Deno tizimda topilmadi. Iltimos o'rnating: irm https://deno.land/install.ps1 | iex")

            cmd = [
                deno_executable, "run", "--allow-read", "--allow-write",
                self.script_path,
                spec_path,
                pdf_path
            ]
            
            logger.info(f"PDF generatsiya qilinmoqda: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Deno PDF generatsiya xatoligi: {stderr.decode('utf-8')}")
                raise RuntimeError("PDF fayl generatsiya qilishda xatolik yuz berdi.")
                
            # 3. Yaratilgan PDF faylni baytlar sifatida o'qish
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
                
            return pdf_bytes
            
        finally:
            # 4. Vaqtinchalik fayllarni o'chirish (tozalash)
            if os.path.exists(spec_path):
                os.remove(spec_path)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

# Qulaylik uchun tayyor obyekt
pdf_service = PDFGeneratorService()
