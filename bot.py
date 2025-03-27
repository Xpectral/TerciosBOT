import json
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import os

# Configura tus credenciales desde variables de entorno
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]"1234567890:ABCDefghIJKLMNOP-YourBotTokenHere"  # Sustituye por tu token

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

app = Client("hntercios_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ID del administrador principal para enviar notificaciones
ADMIN_USER_ID = int(os.environ.get("ADMIN_USER_ID", 0))

async def notify_admin_on_start():
    if ADMIN_USER_ID:
        try:
            await app.send_message(ADMIN_USER_ID, "✅ El bot de HηTercios ha arrancado correctamente.")
        except Exception as e:
            print(f"[ERROR] No se pudo notificar al admin: {e}")

# Diccionario para evitar spam del mensaje de advertencia
warning_messages = {}


def save_silenced_topics():
    with open(PERSISTENCE_FILE, "w") as f:
        json.dump(list(silenced_topics), f)


def is_admin(user_id, chat_member):
    return chat_member.status in ("administrator", "creator")


@app.on_message(filters.command("panel") & filters.group)
async def show_control_panel(client, message: Message):
    if not message.from_user:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id
    chat_member = await app.get_chat_member(chat_id, user_id)

    if not is_admin(user_id, chat_member):
        await message.reply("Solo los administradores pueden usar este comando.")
        return

    topic_id = message.message_thread_id

    if not topic_id:
        await message.reply("Este comando debe ejecutarse dentro del subtema que quieres gestionar.")
        return

    estado = "Desilenciar" if topic_id in silenced_topics else "Silenciar"
    boton = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{estado} este subtema ⚔️", callback_data=f"toggle_{topic_id}")],
        [InlineKeyboardButton("🔍 Ver subtemas silenciados", callback_data="ver_silenciados")]
    ])

    await message.reply("🔧 Panel de control del subtema HηTercios\n✨ Invoca el cosmos para proteger este canal ✨", reply_markup=boton)


@app.on_callback_query()
async def handle_callback(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    if data == "ver_silenciados":
        if not silenced_topics:
            await callback_query.message.edit_text("📭 No hay subtemas silenciados actualmente.")
            return

        lines = ["🔇 Subtemas silenciados:"]
        for tid in silenced_topics:
            try:
                topic_info = await client.get_forum_topic(chat_id, tid)
                lines.append(f"- {topic_info.name} (ID: `{tid}`)")
            except:
                lines.append(f"- ID del subtema: `{tid}` (nombre no disponible)")

        await callback_query.message.edit_text("\n".join(lines))
        return

    if not data.startswith("toggle_"):
        return

    topic_id = int(data.split("_")[1])
    chat_member = await app.get_chat_member(chat_id, user_id)

    if not is_admin(user_id, chat_member):
        await callback_query.answer("Solo los administradores pueden hacer esto.", show_alert=True)
        return

    if topic_id in silenced_topics:
        silenced_topics.remove(topic_id)
        save_silenced_topics()
        await callback_query.message.edit_text("✅ Este subtema ya no está silenciado. Todos pueden escribir.\n🌟 El cosmos fluye libremente.")
    else:
        silenced_topics.add(topic_id)
        save_silenced_topics()
        await callback_query.message.edit_text("🔇 Este subtema ha sido silenciado. Solo administradores pueden escribir.\n🛡️ Protegido por los Caballeros del Silencio.")


@app.on_message(filters.command("silenciar") & filters.group)
async def set_silenced_topics(client, message: Message):
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


@app.on_message(filters.command("silenciados") & filters.group)
async def list_silenced_topics(client, message: Message):
    if not silenced_topics:
        await message.reply("📭 No hay subtemas silenciados actualmente.")
        return

    lines = [f"🔇 Subtemas silenciados:"]
    for tid in silenced_topics:
        try:
            topic_info = await client.get_forum_topic(message.chat.id, tid)
            lines.append(f"- {topic_info.name} (ID: `{tid}`)")
        except:
            lines.append(f"- ID del subtema: `{tid}` (nombre no disponible)")

    await message.reply("\n".join(lines))


@app.on_message(filters.group & filters.text)
async def auto_delete(client, message: Message):
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

    # Enviar advertencia si han pasado al menos 10 segundos desde la última
    if now - last_warning > 10:
        warning_messages[topic_id] = now
        msg = await client.send_message(
            chat_id,
            "⚠️ Canal solo lectura",
            message_thread_id=topic_id
        )
        await asyncio.sleep(10)
        await msg.delete()


async def main():
    await notify_admin_on_start()
    await app.start()
    await idle()

from pyrogram.idle import idle

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[ERROR] Fallo crítico al arrancar el bot: {e}")
        if ADMIN_USER_ID:
            asyncio.run(app.send_message(ADMIN_USER_ID, f"❌ El bot de HηTercios ha fallado al iniciar:
{e}"))
