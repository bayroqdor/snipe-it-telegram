import asyncio
from services.snipe_it import snipe_client

async def main():
    try:
        user = await snipe_client.get_user(235)
        print("User data keys:", user.keys() if user else "None")
        print("Name:", user.get("name"))
        print("First name:", user.get("first_name"))
        print("Last name:", user.get("last_name"))
        print("Full object:", user)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
