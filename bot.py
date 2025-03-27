import json
import os
import asyncio
from datetime import datetime, timezone
from pyrogram import Client, filters, enums  # Importa enums aquí

# Configuración
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_USER_ID = int(os.environ.get("ADMIN_USER_ID", 0))

app = Client("hntercios_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Variables globales
PERSISTENCE_FILE = "silenced_topics.json"
warning_messages = {}

# Funciones auxiliares
def load_silenced_topics():
    try:
        if os.path.exists(PERSISTENCE_FILE):
            with open(PERSISTENCE_FILE, "r") as f:
                data = f.read().strip()
                return set(json.loads(data)) if data else set()
        return set()
    except Exception as e:
        print(f"Error cargando silenced_topics: {e}")
        return set()

def save_silenced_topics(topics):
    try:
        with open(PERSISTENCE_FILE, "w") as f:
            json.dump(list(topics), f)
    except Exception as e:
        print(f"Error guardando silenced_topics: {e}")

async def notify_admin(message):
    if ADMIN_USER_ID:
        try:
            await app.send_message(ADMIN_USER_ID, message)
        except Exception as e:
            print(f"Error notificando al admin: {e}")

# Comando /start
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    welcome_msg = (
        "🤖 **Bienvenido al Caballero HηTercios**\n"
        "Guardían de los subtemas del foro\n\n"
        "⚙️ Usa /help para ver los comandos disponibles\n"
        "🌌 El cosmos está en equilibrio"
    )
    await message.reply(welcome_msg, parse_mode=enums.ParseMode.MARKDOWN)

# Comando /status
@app.on_message(filters.command("status") & (filters.private | filters.group))
async def status_command(client, message):
    try:
        silenced_topics = load_silenced_topics()
        info = (
            "✨ *Estado del bot HηTercios* ✨\n"
            f"📂 Subtemas silenciados: `{len(silenced_topics)}`\n"
            f"🕒 Última actividad: `{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC`\n"
            "🧪 Versión: `1.0.0`\n"
            "🌌 Cosmos activo y fluyendo 🛡️"
        )
        await message.reply(info, parse_mode=enums.ParseMode.MARKDOWN)
    except Exception as e:
        await notify_admin(f"❌ Error en /status: {str(e)}")

# Resto de comandos con la misma corrección...

if __name__ == "__main__":
    app.run()
