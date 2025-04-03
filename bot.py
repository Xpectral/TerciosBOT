import json
import logging
import os
from datetime import datetime, timezone
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Variables de entorno
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Token del bot (configurado en Railway)
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')       # ID del administrador (configurado en Railway)

# Archivo para persistencia de subtemas silenciados
SILENCED_FILE = "silenced_topics.json"

# Última actividad del bot
last_activity = datetime.now(timezone.utc)

# Lista de subtemas silenciados
silenced_topics = []

def save_silenced_topics():
    """Guarda los subtemas silenciados en un archivo JSON."""
    with open(SILENCED_FILE, 'w', encoding='utf-8') as file:
        json.dump(silenced_topics, file, ensure_ascii=False, indent=4)

def load_silenced_topics():
    """Carga los subtemas silenciados desde un archivo JSON."""
    global silenced_topics
    if os.path.exists(SILENCED_FILE):
        with open(SILENCED_FILE, 'r', encoding='utf-8') as file:
            silenced_topics = json.load(file)
    else:
        silenced_topics = []

def update_last_activity():
    """Actualiza la última actividad del bot."""
    global last_activity
    last_activity = datetime.now(timezone.utc)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start."""
    update_last_activity()
    await update.message.reply_text(
        '🤖 *Bienvenido al Caballero HηTercios*\n'
        'Guardián de los subtemas del foro.\n\n'
        '⚙️ Usa /help para ver los comandos disponibles.\n'
        '🌌 El cosmos está en equilibrio.',
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help."""
    update_last_activity()
    await update.message.reply_text(
        '*Comandos disponibles:*\n\n'
        '/start - Inicia la conversación con el bot.\n'
        '/status - Muestra el estado del bot.\n'
        '/silenciar - Silencia un subtema.\n'
        '/silenciados - Lista los subtemas silenciados.\n'
        '/help - Muestra este mensaje de ayuda.',
        parse_mode=ParseMode.MARKDOWN
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status."""
    update_last_activity()
    silenced_count = len(silenced_topics)
    last_activity_str = last_activity.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    await update.message.reply_text(
        f'✨ *Estado del bot HηTercios* ✨\n'
        f'📂 Subtemas silenciados: `{silenced_count}`\n'
        f'🕒 Última actividad: `{last_activity_str}`\n'
        f'🌌 Cosmos activo y fluyendo 🛡️',
        parse_mode=ParseMode.MARKDOWN
    )

async def silenciar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /silenciar."""
    update_last_activity()
    
    if not hasattr(update.message, 'is_topic_message') or not update.message.is_topic_message:
        await update.message.reply_text(
            '❌ Este comando solo puede usarse dentro de un subtema.',
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    user = update.effective_user
    chat = update.effective_chat
    
    admins = await context.bot.get_chat_administrators(chat.id)
    is_admin = user.id in [admin.user.id for admin in admins]
    
    if not is_admin:
        await update.message.reply_text(
            '❌ Solo los administradores pueden usar este comando.',
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    topic_id = update.message.message_thread_id
    
    if topic_id in silenced_topics:
        silenced_topics.remove(topic_id)
        save_silenced_topics()
        await update.message.reply_text(
            '✅ Este subtema ya no está silenciado. Todos pueden escribir.',
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        silenced_topics.append(topic_id)
        save_silenced_topics()
        await update.message.reply_text(
            '🔇 Este subtema ha sido silenciado. Solo administradores pueden escribir.',
            parse_mode=ParseMode.MARKDOWN
        )

async def silenciados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /silenciados."""
    update_last_activity()
    
    if not silenced_topics:
        await update.message.reply_text(
            '📂 No hay subtemas silenciados actualmente.',
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    response = '📂 *Subtemas silenciados:*\n'
    for topic_id in silenced_topics:
        response += f'- Subtema (ID: `{topic_id}`)\n'
    
    await update.message.reply_text(
        response,
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Monitoreo de mensajes en subtemas silenciados."""
    update_last_activity()
    
    if (update.message and 
        hasattr(update.message, 'is_topic_message') and 
        update.message.is_topic_message and 
        hasattr(update.message, 'message_thread_id') and 
        update.message.message_thread_id in silenced_topics):
        
        user = update.effective_user
        chat = update.effective_chat
        
        admins = await context.bot.get_chat_administrators(chat.id)
        
        is_admin = user.id in [admin.user.id for admin in admins]
        
        if not is_admin:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
            
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                message_thread_id=update.message.message_thread_id,
                text='⚠️ Este subtema está en modo solo lectura.',
                parse_mode=ParseMode.MARKDOWN
            )

def main():
    """Inicialización del bot."""
    
    # Verificar que TELEGRAM_TOKEN esté definido.
    if not TELEGRAM_TOKEN:
        raise ValueError("La variable TELEGRAM_BOT_TOKEN no está definida. Configúrala en Railway.")
    
    load_silenced_topics()
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("silenciar", silenciar))
    application.add_handler(CommandHandler("silenciados", silenciados))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling()

if __name__ == '__main__':
    main()
