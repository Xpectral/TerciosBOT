import json
import os
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from datetime import datetime

# Configuración desde variables de entorno
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_USER_ID = int(os.environ.get("ADMIN_USER_ID", 0))

app = Client("hntercios_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Persistencia de temas silenciados
PERSISTENCE_FILE = "silenced_topics.json"
warning_messages = {}  # Diccionario para control de advertencias

def load_silenced_topics():
    try:
        if os.path.exists(PERSISTENCE_FILE):
            with open(PERSISTENCE_FILE, "r") as f:
                return set(json.load(f))
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
async def start_command(client, message: Message):
    welcome_msg = (
        "🤖 **Bienvenido al Caballero HηTercios**\n"
        "Guardían de los subtemas del foro\n\n"
        "⚙️ Usa /help para ver los comandos disponibles\n"
        "🌌 El cosmos está en equilibrio"
    )
    await message.reply(welcome_msg, parse_mode="markdown")

# Comando /silenciar
@app.on_message(filters.command("silenciar") & filters.group)
async def toggle_silence(client, message: Message):
    if not message.from_user or not message.message_thread_id:
        return
    
    user = await app.get_chat_member(message.chat.id, message.from_user.id)
    if user.status not in ["administrator", "creator"]:
        await message.reply("⚠️ Solo administradores pueden usar este comando")
        return
    
    silenced = load_silenced_topics()
    topic_id = message.message_thread_id
    
    if topic_id in silenced:
        silenced.remove(topic_id)
        response = "✅ Subtema reactivado\n🌟 El cosmos fluye libremente"
    else:
        silenced.add(topic_id)
        response = "🔇 Subtema silenciado\n🛡️ Protegido por los Caballeros"
    
    save_silenced_topics(silenced)
    await message.reply(response)

# Autoeliminación mejorada
@app.on_message(filters.group & filters.text)
async def enforce_silence(client, message: Message):
    if not message.from_user or not message.message_thread_id:
        return
    
    topic_id = message.message_thread_id
    if topic_id not in load_silenced_topics():
        return
    
    user = await app.get_chat_member(message.chat.id, message.from_user.id)
    if user.status in ["administrator", "creator"]:
        return
    
    await message.delete()
    now = asyncio.get_event_loop().time()
    
    if now - warning_messages.get(topic_id, 0) > 10:
        warning = await client.send_message(
            message.chat.id,
            "⚠️ **Este canal es solo lectura**\n"
            "Solo los administradores pueden publicar aquí",
            message_thread_id=topic_id
        )
        warning_messages[topic_id] = now
        await asyncio.sleep(10)
        await warning.delete()

async def main():
    try:
        await app.start()
        await notify_admin("✅ Bot activado correctamente")
        print("Bot en funcionamiento")
        
        # Mantener el bot activo escuchando eventos
        idle()
        
    except Exception as e:
        print(f"Error crítico: {e}")
        try:
            await notify_admin(f"❌ Error crítico: {str(e)}")
        except Exception as notify_error:
            print(f"Error notificando al admin sobre el error crítico: {notify_error}")
    finally:
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
