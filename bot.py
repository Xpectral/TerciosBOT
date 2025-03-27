import json
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime

# Configuración desde variables de entorno
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_USER_ID = int(os.environ.get("ADMIN_USER_ID", 0))

# Inicializa el cliente
app = Client("hntercios_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Ruta del archivo de persistencia
PERSISTENCE_FILE = "silenced_topics.json"

# Diccionario para advertencias
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
        print(f"[ERROR] No se pudo cargar silenced_topics.json: {e}")
        return set()

def save_silenced_topics(silenced_topics):
    try:
        with open(PERSISTENCE_FILE, "w") as f:
            json.dump(list(silenced_topics), f)
    except Exception as e:
        print(f"[ERROR] No se pudo guardar silenced_topics.json: {e}")

async def notify_admin(message):
    if ADMIN_USER_ID:
        try:
            await app.send_message(ADMIN_USER_ID, message)
        except Exception as e:
            print(f"[ERROR] No se pudo notificar al admin: {e}")

# Handlers de comandos
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    welcome_msg = (
        "🤖 **Bienvenido al Caballero HηTercios**\n"
        "Guardían de los subtemas del foro\n\n"
        "⚙️ Usa /help para ver los comandos disponibles\n"
        "🌌 El cosmos está en equilibrio"
    )
    await message.reply(welcome_msg, parse_mode="markdown")

@app.on_message(filters.command("status") & (filters.private | filters.group))
async def status_command(client, message: Message):
    silenced_topics = load_silenced_topics()
    info = (
        "✨ *Estado del bot HηTercios* ✨\n"
        f"📂 Subtemas silenciados: `{len(silenced_topics)}`\n"
        f"🕒 Última actividad: `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`\n"
        "🌌 Cosmos activo y fluyendo 🛡️"
    )
    await message.reply(info, parse_mode="markdown")

@app.on_message(filters.command("silenciar") & filters.group)
async def toggle_silence(client, message: Message):
    silenced_topics = load_silenced_topics()
    try:
        if not message.from_user or not message.message_thread_id:
            return
        user_id = message.from_user.id
        chat_member = await app.get_chat_member(message.chat.id, user_id)
        if chat_member.status not in ["administrator", "creator"]:
            await message.reply("⚠️ Solo administradores pueden usar este comando.")
            return
        
        topic_id = message.message_thread_id
        if topic_id in silenced_topics:
            silenced_topics.remove(topic_id)
            save_silenced_topics(silenced_topics)
            await message.reply("✅ Este subtema ya no está silenciado. Todos pueden escribir.")
        else:
            silenced_topics.add(topic_id)
            save_silenced_topics(silenced_topics)
            await message.reply("🔇 Este subtema ha sido silenciado. Solo administradores pueden escribir.")
    except Exception as e:
        await notify_admin(f"❌ Error en /silenciar:\n{str(e)}")

@app.on_message(filters.group & filters.text)
async def auto_delete(client, message: Message):
    silenced_topics = load_silenced_topics()
    try:
        if not message.message_thread_id or message.message_thread_id not in silenced_topics:
            return
        
        chat_member = await app.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status in ["administrator", "creator"]:
            return
        
        await message.delete()
        
        topic_id = message.message_thread_id
        now = datetime.utcnow().timestamp()
        
        if topic_id not in warning_messages or now - warning_messages[topic_id] > 10:
            warning_messages[topic_id] = now
            msg = await client.send_message(
                chat_id=message.chat.id,
                text="⚠️ **Canal solo lectura**",
                message_thread_id=topic_id,
                parse_mode="markdown"
            )
            await asyncio.sleep(10)
            await msg.delete()
    except Exception as e:
        await notify_admin(f"❌ Error en auto_delete:\n{str(e)}")

# Ejecución del bot
if __name__ == "__main__":
    try:
        app.run()  # Usa app.run() para iniciar correctamente el cliente y manejar idle automáticamente.
    except Exception as e:
        print(f"[ERROR] Fallo crítico al arrancar el bot: {e}")
