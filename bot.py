import json
import os
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions

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
@app.on_message(filters.command("start") & filters.group)
async def start_command(client, message):
    print("[INFO] Comando /start recibido")
    welcome_msg = (
        "🤖 **Bienvenido al Caballero HηTercios**\n"
        "Guardían de los subtemas del foro\n\n"
        "⚙️ Usa /help para ver los comandos disponibles\n"
        "🌌 El cosmos está en equilibrio"
    )
    await message.reply(welcome_msg, parse_mode="markdown")

# Comando /help
@app.on_message(filters.command("help") & filters.group)
async def help_command(client, message):
    print("[INFO] Comando /help recibido")
    help_msg = (
        "**Comandos disponibles:**\n\n"
        "/start - Inicia la conversación con el bot.\n"
        "/status - Muestra el estado del bot.\n"
        "/silenciar - Silencia un subtema (solo dentro de temas).\n"
        "/silenciados - Lista los subtemas silenciados.\n"
        "/help - Muestra este mensaje de ayuda.\n"
    )
    await message.reply(help_msg, parse_mode="markdown")

# Comando /status
@app.on_message(filters.command("status") & filters.group)
async def status_command(client, message):
    print("[INFO] Comando /status recibido")
    try:
        silenced_topics = load_silenced_topics()
        info = (
            "✨ *Estado del bot HηTercios* ✨\n"
            f"📂 Subtemas silenciados: `{len(silenced_topics)}`\n"
            f"🕒 Última actividad: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC`\n"
            "🌌 Cosmos activo y fluyendo 🛡️"
        )
        await message.reply(info, parse_mode="markdown")
    except Exception as e:
        print(f"[ERROR] Error en /status: {e}")
        await message.reply("❌ Error al obtener el estado del bot")

# Comando /silenciar
@app.on_message(filters.command("silenciar") & filters.group)
async def toggle_silence(client, message):
    print("[INFO] Comando /silenciar recibido")
    try:
        # Verificar si el mensaje pertenece a un tema
        if not hasattr(message, 'message_thread_id') or not message.message_thread_id:
            await message.reply("⚠️ Este comando solo funciona en temas.")
            return
        
        user_id = message.from_user.id
        chat_member = await app.get_chat_member(message.chat.id, user_id)
        
        # Verificar si el usuario es administrador
        if chat_member.status not in ["administrator", "creator"]:
            await message.reply("⚠️ Solo administradores pueden usar este comando.")
            return
        
        # Alternar estado del tema
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

# Comando /silenciados
@app.on_message(filters.command("silenciados") & filters.group)
async def list_silenced(client, message):
    print("[INFO] Comando /silenciados recibido")
    try:
        silenced_topics = load_silenced_topics()
        
        if not silenced_topics:
            await message.reply("📂 No hay subtemas silenciados actualmente.")
            return
        
        topics_list = "\n".join([f"- Subtema ID: `{topic}`" for topic in silenced_topics])
        await message.reply(f"📂 *Subtemas silenciados:*\n{topics_list}", parse_mode="markdown")

# Monitoreo de mensajes en subtemas silenciados
@app.on_message(filters.group & filters.text)
async def monitor_silenced_topics(client, message):
    try:
        if hasattr(message, 'message_thread_id') and message.message_thread_id:
            silenced_topics = load_silenced_topics()
            topic_id = message.message_thread_id
            
            if topic_id in silenced_topics:
                user_id = message.from_user.id
                chat_member = await app.get_chat_member(message.chat.id, user_id)
                
                if chat_member.status not in ["administrator", "creator"]:
                    await message.delete()
                    if topic_id not in warning_messages:
                        warning_messages[topic_id] = time.time()
                        await message.reply("⚠️ Este subtema está en modo solo lectura.")
                    else:
                        if time.time() - warning_messages[topic_id] > 60:  # Mensaje de advertencia cada minuto
                            warning_messages[topic_id] = time.time()
                            await message.reply("⚠️ Este subtema está en modo solo lectura.")
    except Exception as e:
        print(f"[ERROR] Error en monitor_silenced_topics: {e}")

if __name__ == "__main__":
    app.run()
