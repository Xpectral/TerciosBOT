import json
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime

# Configuración desde variables de entorno
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_USER_ID = int(os.environ.get("ADMIN_USER_ID", 0))

app = Client("hntercios_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ... (resto del código sin cambios)

async def notify_admin(message):
    if ADMIN_USER_ID:
        try:
            await app.send_message(ADMIN_USER_ID, message)
        except Exception as e:
            print(f"Error notificando al admin: {e}")

async def main():
    try:
        await app.start()
        await notify_admin("✅ Bot activado correctamente")
        print("Bot en funcionamiento")
        await app.idle()
    except Exception as e:
        print(f"Error crítico: {e}")
        try:
            await notify_admin(f"❌ Error crítico: {str(e)}")
        except:
            print("No se pudo notificar al admin sobre el error crítico")
    finally:
        await app.stop()

if __name__ == "__main__":
    app.run(main())
