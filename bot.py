import json
import os
from datetime import datetime, timezone
from pyrogram import Client, filters, enums

# Configuración desde variables de entorno
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_USER_ID = int(os.environ.get("ADMIN_USER_ID", 0))

# Inicializa el cliente
app = Client("hntercios_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Variables globales
PERSISTENCE_FILE = "silenced_topics.json"
warning_messages = {}

# Funciones auxiliares
def load_silenced_topics():
    """Carga los temas silenciados desde un archivo JSON."""
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
    """Guarda los temas silenciados en un archivo JSON."""
    try:
        with open(PERSISTENCE_FILE, "w") as f:
            json.dump(list(silenced_topics), f)
    except Exception as e:
        print(f"[ERROR] No se pudo guardar silenced_topics.json: {e}")

async def notify_admin(message):
    """Envía una notificación al administrador."""
    if ADMIN_USER_ID:
        try:
            await app.send_message(ADMIN_USER_ID, message)
        except Exception as e:
            print(f"[ERROR] No se pudo notificar al admin: {e}")

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

# Comando /help
@app.on_message(filters.command("help") & (filters.private | filters.group))
async def help_command(client, message):
    help_msg = (
        "**Comandos disponibles:**\n\n"
        "/start - Inicia la conversación con el bot.\n"
        "/status - Muestra el estado del bot.\n"
        "/silenciar - Silencia un subtema (solo dentro de temas de foro).\n"
        "/silenciados - Lista los subtemas silenciados.\n"
        "/help - Muestra este mensaje de ayuda.\n"
    )
    await message.reply(help_msg, parse_mode=enums.ParseMode.MARKDOWN)

# Comando /status
@app.on_message(filters.command("status") & (filters.private | filters.group))
async def status_command(client, message):
    try:
        silenced_topics = load_silenced_topics()
        info = (
            "✨ *Estado del bot HηTercios* ✨\n"
            f"📂 Subtemas silenciados: `{len(silenced_topics)}`\n"
            f"🕒 Última actividad: `{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC`\n"
            "🌌 Cosmos activo y fluyendo 🛡️"
        )
        await message.reply(info, parse_mode=enums.ParseMode.MARKDOWN)
    except Exception as e:
        print(f"[ERROR] Error en /status: {e}")
        await message.reply("❌ Error al obtener el estado del bot")

# Comando /silenciar
@app.on_message(filters.command("silenciar") & filters.group)
async def toggle_silence(client, message):
    try:
        if not hasattr(message, 'message_thread_id') or not message.message_thread_id:
            await message.reply("⚠️ Este comando solo funciona en temas de foro.")
            return
        
        user_id = message.from_user.id
        chat_member = await app.get_chat_member(message.chat.id, user_id)
        
        if chat_member.status not in ["administrator", "creator"]:
            await message.reply("⚠️ Solo administradores pueden usar este comando.")
            return
        
        silenced_topics = load_silenced_topics()
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
        print(f"[ERROR] Error en /silenciar: {e}")
        await notify_admin(f"❌ Error en /silenciar:\n{str(e)}")

# Comando /silenciados
@app.on_message(filters.command("silenciados") & filters.group)
async def list_silenced(client, message):
    try:
        silenced_topics = load_silenced_topics()
        
        if not silenced_topics:
            await message.reply("📂 No hay subtemas silenciados actualmente.")
            return
        
        topics_list = "\n".join([f"- Subtema ID: `{topic}`" for topic in silenced_topics])
        await message.reply(f"📂 *Subtemas silenciados:*\n{topics_list}", parse_mode=enums.ParseMode.MARKDOWN)
    except Exception as e:
        print(f"[ERROR] Error en /silenciados: {e}")
        await notify_admin(f"❌ Error en /silenciados:\n{str(e)}")

# Autoeliminación de mensajes en temas silenciados
@app.on_message(filters.group & ~filters.command())
async def auto_delete(client, message):
    try:
        if not hasattr(message, 'message_thread_id') or not message.message_thread_id or message.message_thread_id not in load_silenced_topics():
            return
        
        chat_member = await app.get_chat_member(message.chat.id, message.from_user.id)
        
        if chat_member.status in ["administrator", "creator"]:
            return
        
        await message.delete()
        
        topic_id = message.message_thread_id
        now = datetime.now(timezone.utc).timestamp()
        
        if topic_id not in warning_messages or now - warning_messages.get(topic_id, 0) > 10:
            warning_messages[topic_id] = now
            warning = await client.send_message(
                chat_id=message.chat.id,
                text="⚠️ **Canal solo lectura**\nSolo los administradores pueden escribir aquí",
                message_thread_id=topic_id,
                parse_mode=enums.ParseMode.MARKDOWN
            )
            await asyncio.sleep(10)
            try:
                await warning.delete()
            except Exception as e:
                print(f"[ERROR] Error al eliminar advertencia: {e}")
    except Exception as e:
        print(f"[ERROR] Error en auto_delete: {e}")

# Ejecución del bot
if __name__ == "__main__":
    try:
        print("[INFO] Iniciando bot HηTercios...")
        
        app.run()  # Inicia el cliente y maneja el ciclo de eventos automáticamente.
    except Exception as e:
        print(f"[ERROR] Fallo crítico al arrancar el bot: {e}")
