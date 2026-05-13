import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from utils.config import Config
from utils.logger import logger

class SnipeITClient:
    """Snipe-IT API bilan ishlash uchun asinxron mijoz klassi."""
    
    def __init__(self):
        self.base_url = Config.SNIPE_IT_URL
        self.headers = {
            "Authorization": f"Bearer {Config.SNIPE_IT_API_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Ichki yordamchi metod API ga so'rov yuborish uchun."""
        url = f"{self.base_url}/api/v1/{endpoint.lstrip('/')}"
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.request(method, url, params=params) as response:
                    # Agar xatolik bo'lsa HTTPException ni ko'taradi (raise_for_status)
                    response.raise_for_status()
                    data = await response.json()
                    return data
        except aiohttp.ClientResponseError as e:
            logger.error(f"Snipe-IT API Xatoligi: {e.status} - {e.message} (URL: {url})")
            raise
        except Exception as e:
            logger.error(f"Snipe-IT API ulanishida xatolik: {str(e)} (URL: {url})")
            raise

    async def search_users(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Ism yoki username bo'yicha xodimlarni qidirish."""
        if not query:
            return []
            
        params = {"search": query, "limit": limit}
        data = await self._request("GET", "users", params=params)
        return data.get("rows", [])

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Xodim haqida to'liq ma'lumot olish."""
        data = await self._request("GET", f"users/{user_id}")
        # API "status": "success" kabi javob qaytarishi yoki to'g'ridan to'g'ri user obyekti qaytishi mumkin
        if "id" in data:
            return data
        return data.get("payload") # payload kalitini tekshirish (Snipe-IT versiyasiga qarab)
        
    async def get_user_assets(self, user_id: int) -> List[Dict[str, Any]]:
        """Xodimga biriktirilgan aktivlarni olish."""
        data = await self._request("GET", f"users/{user_id}/assets")
        return data.get("rows", [])

    async def get_user_licenses(self, user_id: int) -> List[Dict[str, Any]]:
        """Xodimga biriktirilgan litsenziyalarni olish va ularning izohlarini (checkout notes) qo'shish."""
        data = await self._request("GET", f"users/{user_id}/licenses")
        licenses = data.get("rows", [])
        
        if not licenses:
            return []

        async def fetch_seat_note(lic: Dict[str, Any]):
            try:
                seats_data = await self._request("GET", f"licenses/{lic['id']}/seats")
                for seat in seats_data.get("rows", []):
                    assigned_user = seat.get("assigned_user")
                    if assigned_user and assigned_user.get("id") == user_id:
                        lic["notes"] = seat.get("notes") or ""
                        break
            except Exception as e:
                logger.error(f"License seats olishda xatolik (License ID: {lic.get('id')}): {e}")

        # Barcha litsenziyalarning seatlarini parallel ravishda tortib olamiz
        await asyncio.gather(*(fetch_seat_note(lic) for lic in licenses))
        
        return licenses

    async def get_user_accessories(self, user_id: int) -> List[Dict[str, Any]]:
        """Xodimga biriktirilgan aksessuarlarni olish."""
        data = await self._request("GET", f"users/{user_id}/accessories")
        return data.get("rows", [])

    async def get_full_user_report(self, user_id: int) -> Dict[str, Any]:
        """Xodim haqidagi hamma ma'lumotlarni parallel tarzda yuklab olish."""
        try:
            # Parallel so'rovlarni jo'natish
            user_task = self.get_user(user_id)
            assets_task = self.get_user_assets(user_id)
            licenses_task = self.get_user_licenses(user_id)
            accessories_task = self.get_user_accessories(user_id)
            
            user_data, assets, licenses, accessories = await asyncio.gather(
                user_task, assets_task, licenses_task, accessories_task
            )
            
            return {
                "user": user_data,
                "assets": assets,
                "licenses": licenses,
                "accessories": accessories
            }
        except Exception as e:
            logger.error(f"Foydalanuvchi ma'lumotlarini yuklashda xato (ID: {user_id}): {str(e)}")
            raise

# Qulaylik uchun tayyor obyekt
snipe_client = SnipeITClient()
