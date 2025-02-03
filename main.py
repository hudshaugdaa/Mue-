import time
import threading
import datetime
import json
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext


# Configuração do bot
TOKEN = "8030812928:AAEVr29_1LcUDCOEsZFipOprv0QZ30uAOwM"
ADMIN_ID = 5650303115  # ID do administrador
CONFIG_FILE = "config.json"  # Arquivo para salvar os links
GROUPS_FILE = "groups.json"  # Arquivo para salvar grupos permitidos
AUTO_MODE = False  # Ligamento automático
START_TIME = "08:00"
STOP_TIME = "22:00"
running = False  # Controle do envio de mensagens

# Criar arquivos JSON automaticamente se não existirem
def ensure_json_file(file_path, default_data):
    try:
        with open(file_path, "r") as f:
            data = f.read().strip()
            if not data:
                raise ValueError("Arquivo JSON vazio")
            return json.loads(data)
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        with open(file_path, "w") as f:
            json.dump(default_data, f, indent=4)
        return default_data

# Carregar configurações e grupos
config = ensure_json_file(CONFIG_FILE, {
    "LINK_METODO": "https://seu-link-do-metodo.com",
    "LINK_BOT": "https://seu-link-do-bot.com"
})

PERMITTED_GROUPS = ensure_json_file(GROUPS_FILE, [])

# Inicia a aplicação do bot
application = Application.builder().token(TOKEN).build()

# Comando /start
async def start(update: Update, context: CallbackContext):
    global running
    chat_id = update.effective_chat.id

    if chat_id not in PERMITTED_GROUPS:
        await update.message.reply_text("🚫 Este grupo não está autorizado para usar este bot.")
        return

    if not running:
        running = True
        await update.message.reply_text("🚀 Bot Iniciado! Enviando sinais...")
        threading.Thread(target=send_messages, args=(application,)).start()
    else:
        await update.message.reply_text("⚠️ O bot já está rodando!")

# Comando /stop
async def stop(update: Update, context: CallbackContext):
    global running
    chat_id = update.effective_chat.id

    if chat_id != ADMIN_ID:
        await update.message.reply_text("🚫 Apenas o administrador pode parar o bot.")
        return

    running = False
    await update.message.reply_text("🛑 Bot parado!")

# Função assíncrona para enviar mensagens
async def send_signal(app, group_id, message):
    try:
        await app.bot.send_message(chat_id=group_id, text=message, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        print(f"Erro ao enviar mensagem para {group_id}: {e}")

# Função para enviar sinais
def send_messages(app):
    global running
    count = 0
    messages_above = 2
    messages_below = 2

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while running:
        now = datetime.datetime.now()
        valid_until = now + datetime.timedelta(minutes=1)
        valid_until_str = valid_until.strftime("%H:%M")

        if count < messages_above:
            message = f"""
🟩 **Acima de 2x**
🔴 **Botão 1:** 1.60
🔴 **Botão 2:** (Lucro variável)


🔍 **Método Secreto:** 1X60 e Velas  
🔗 [Clique Aqui]({config['LINK_METODO']})

🟢 **Esse robô só funciona aqui:**  
🔗 [Acesse Agora]({config['LINK_BOT']})
"""
        elif count < messages_above + messages_below:
            message = f"""
🆘 **ABAIXO DE 2x**
🔴 **Botão 1:** 1.60
⚠️ **50/50 Chance**

🔍 **Método Secreto:** 1X60 e Velas  
🔗 [Clique Aqui]({config['LINK_METODO']})

🟢 **Esse robô só funciona aqui:**  
🔗 [Acesse Agora]({config['LINK_BOT']})
"""
        else:
            count = -1  # Reseta a contagem

        for group_id in PERMITTED_GROUPS:
            loop.run_until_complete(send_signal(app, group_id, message))

        count += 1
        time.sleep(60)

# Comando /admin
async def admin(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    if chat_id != ADMIN_ID:
        await update.message.reply_text("🚫 Apenas o administrador pode acessar o painel.")
        return

    auto_status = "✅ Ativado" if AUTO_MODE else "❌ Desativado"
    groups_list = "\n".join([str(g) for g in PERMITTED_GROUPS]) if PERMITTED_GROUPS else "Nenhum"

    message = f"""
🔧 **Painel de Administração**
🕒 **Ligamento Automático:** {auto_status}
⏰ **Horário:** {START_TIME} - {STOP_TIME}
👥 **Grupos Permitidos:**  
{groups_list}

🔗 **Links Atuais:**  
📌 Método Secreto: {config['LINK_METODO']}  
📌 Link do Bot: {config['LINK_BOT']}  

⚙️ Comandos:
- `/set_links LINK_METODO LINK_BOT` ➝ Alterar os links  
- `/permit GROUP_ID` ➝ Permitir grupo
- `/deny GROUP_ID` ➝ Bloquear grupo
"""

    await update.message.reply_text(message, parse_mode="Markdown")

# Comando para alterar os links
async def set_links(update: Update, context: CallbackContext):
    if update.effective_chat.id != ADMIN_ID:
        return

    args = context.args
    if len(args) != 2:
        await update.message.reply_text("❌ Uso correto: `/set_links LINK_METODO LINK_BOT`")
        return

    config["LINK_METODO"], config["LINK_BOT"] = args

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    await update.message.reply_text("✅ Links atualizados com sucesso!")

# Comando para permitir um grupo
async def permit(update: Update, context: CallbackContext):
    if update.effective_chat.id != ADMIN_ID:
        return

    args = context.args
    if not args:
        return

    group_id = int(args[0])
    if group_id not in PERMITTED_GROUPS:
        PERMITTED_GROUPS.append(group_id)
        with open(GROUPS_FILE, "w") as f:
            json.dump(PERMITTED_GROUPS, f, indent=4)
        await update.message.reply_text(f"✅ Grupo {group_id} permitido!")

# Comando para bloquear um grupo
async def deny(update: Update, context: CallbackContext):
    if update.effective_chat.id != ADMIN_ID:
        return

    args = context.args
    if not args:
        return

    group_id = int(args[0])
    if group_id in PERMITTED_GROUPS:
        PERMITTED_GROUPS.remove(group_id)
        with open(GROUPS_FILE, "w") as f:
            json.dump(PERMITTED_GROUPS, f, indent=4)
        await update.message.reply_text(f"❌ Grupo {group_id} bloqueado!")

# Iniciar o bot
def main():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("set_links", set_links))
    application.add_handler(CommandHandler("permit", permit))
    application.add_handler(CommandHandler("deny", deny))

    application.run_polling()

if __name__ == "__main__":
    main()