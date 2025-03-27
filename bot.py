import json
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import os

# Configura tus credenciales desde variables de entorno
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_USER_ID = int(os.environ.get("ADMIN_USER_ID", 0))

# Inicializa el bot
app = Client("hntercios_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Ruta del archivo de persistencia
PERSISTENCE_FILE = "silenced_topics.json"

# Cargar temas silenciados desde archivo
try:
    if os.path.exists(PERSISTENCE_FILE):
        with open(PERSISTENCE_FILE, "r") as f:
            data = f.read().strip()
            if data:
                silenced_topics = set(json.loads(data))
            else:
                silenced_topics = set()
    else:
        silenced_topics = set()
        with open(PERSISTENCE_FILE, "w") as f:
            json.dump([], f)
except Exception as e:
    print(f"[ERROR] No se pudo cargar silenced_topics.json: {e}")
    silenced_topics = set()
    with open(PERSISTENCE_FILE, "w") as f:
        json.dump([], f)

# Diccionario para evitar spam del mensaje de advertencia
warning_messages = {}

# Función para guardar los temas silenciados
def save_silenced_topics():
    with open(PERSISTENCE_FILE, "w") as f:
        json.dump(list(silenced_topics), f)

# Verifica si un usuario es administrador
def is_admin(user_id, chat_member):
    return chat_member.status in ("administrator", "creator")

# Notificar al admin al arrancar
async def notify_admin_on_start():
    if ADMIN_USER_ID:
        try:
            await app.start()
            await app.send_message(ADMIN_USER_ID, "✅ El bot de HηTercios ha arrancado correctamente.")
        except Exception as e:
            print(f"[ERROR] No se pudo notificar al admin: {e}")

# Función para notificar errores en ejecución
async def notify_admin_error(context: str, error: Exception):
    if ADMIN_USER_ID:
        try:
            await app.send_message(ADMIN_USER_ID, f"❌ Error en {context}:\n{str(error)}")
        except:
            pass

# Comando /start
@app.on_message(filters.command("start") & filters.private)
async def start(client, message: Message):
    print(f"Comando /start recibido de {message.from_user.id}")  # Log para ver si se recibe el comando
    try:
        await message.reply("¡Hola! Soy tu bot de HηTercios. ¿En qué puedo ayudarte? 🌟")
    except Exception as e:
        print(f"[ERROR] Error al responder al comando /start: {e}")
        await message.reply("Hubo un error al procesar tu comando. 🙁")

# Comando /silenciar
@app.on_message(filters.command("silenciar") & filters.group)
async def set_silenced_topics(client, message: Message):
    try:
        if not message.from_user:
            return

        user_id = message.from_user.id
        chat_id = message.chat.id
        chat_member = await app.get_chat_member(chat_id, user_id)

        if not is_admin(user_id, chat_member):
            await message.reply("Solo los administradores pueden usar este comando.")
            return

        topic_id = message.message_thread_id

        if not topic_id:
            await message.reply("Este comando debe ejecutarse dentro del subtema que quieres silenciar.")
            return

        if topic_id in silenced_topics:
            silenced_topics.remove(topic_id)
            save_silenced_topics()
            await message.reply("✅ Este subtema ya no está silenciado. Todos pueden escribir.\n🌟 El cosmos fluye libremente.")
        else:
            silenced_topics.add(topic_id)
            save_silenced_topics()
            await message.reply("🔇 Este subtema ha sido silenciado. Solo administradores pueden escribir.\n🛡️ Protegido por los Caballeros del Silencio.")
    except Exception as e:
        await notify_admin_error("/silenciar", e)

# Comando /status
@app.on_message(filters.command("status") & (filters.private | filters.group))
async def status_command(client, message: Message):
    try:
        from datetime import datetime
        info = (
            "✨ *Estado del bot HηTercios* ✨\n"
            f"📂 Subtemas silenciados: `{len(silenced_topics)}`\n"
            f"🕒 Última actividad: `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`\n"
            "🧪 Versión: `1.0.0`\n"
            "🌌 Cosmos activo y fluyendo 🛡️"
        )
        await message.reply(info, parse_mode="markdown")
    except Exception as e:
        await notify_admin_error("/status", e)

# Comando /help
@app.on_message(filters.command("help") & (filters.private | filters.group))
async def help_command(client, message: Message):
    try:
        help_text = (
            "📖 *Comandos del Caballero HηTercios:*\n"
            "🔹 `/silenciar` — Silencia el subtema actual (grupo tipo foro, solo admins)\n"
            "🔹 `/silenciados` — Lista los subtemas actualmente silenciados\n"
            "🔹 `/status` — Muestra el estado del cosmos y del bot\n"
            "🔹 `/help` — Muestra esta ayuda celestial"
        )
        await message.reply(help_text, parse_mode="markdown")
    except Exception as e:
        await notify_admin_error("/help", e)

# Comando /silenciados
@app.on_message(filters.command("silenciados") & filters.group)
async def list_silenced_topics(client, message: Message):
    try:
        if not silenced_topics:
            await message.reply("📭 No hay subtemas silenciados actualmente.")
            return

        lines = ["🔇 Subtemas silenciados:"]
        for tid in silenced_topics:
            try:
                topic_info = await client.get_forum_topic(message.chat.id, tid)
                lines.append(f"- {topic_info.name} (ID: `{tid}`)")
            except:
                lines.append(f"- ID del subtema: `{tid}` (nombre no disponible)")

        await message.reply("\n".join(lines))
    except Exception as e:
        await notify_admin_error("/silenciados", e)

# Autoeliminación en subtemas silenciados
@app.on_message(filters.group & filters.text)
async def auto_delete(client, message: Message):
    try:
        if not message.message_thread_id:
            return

        if message.message_thread_id not in silenced_topics:
            return

        chat_id = message.chat.id
        user_id = message.from_user.id
        chat_member = await app.get_chat_member(chat_id, user_id)

        if is_admin(user_id, chat_member):
            return

        await message.delete()

        topic_id = message.message_thread_id
        last_warning = warning_messages.get(topic_id, 0)
        now = asyncio.get_event_loop().time()

        if now - last_warning > 10:
            warning_messages[topic_id] = now
            msg = await client.send_message(
                chat_id,
                "⚠️ Canal solo lectura",
                message_thread_id=topic_id
            )
            await asyncio.sleep(10)
            await msg.delete()
    except Exception as e:
        await notify_admin_error("auto_delete", e)

# Arranque seguro con notificación
async def main():
    await notify_admin_on_start()
    await app.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[ERROR] Fallo crítico al arrancar el bot: {e}")
        if ADMIN_USER_ID:
            try:
                asyncio.run(app.send_message(ADMIN_USER_ID, f"❌ El bot de HηTercios ha fallado al iniciar:\n{e}"))
            except:
                pass
