import os
import subprocess
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)

# Load config
with open("config.json") as f:
    config = json.load(f)

BOT_TOKEN = config["bot_token"]
AUTHORIZED_USERS = config["authorized_users"]
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

user_state = {}

main_menu = ReplyKeyboardMarkup([["Terminal Mode"]], resize_keyboard=True)
terminal_menu = ReplyKeyboardMarkup([["Upload File", "Run Command"]], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Terminal Bot.", reply_markup=main_menu)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if user_id not in AUTHORIZED_USERS:
        return await update.message.reply_text("❌ Unauthorized user.")

    if text == "Terminal Mode":
        user_state[user_id] = "terminal_menu"
        return await update.message.reply_text("Terminal Mode enabled.", reply_markup=terminal_menu)

    elif text == "Upload File":
        user_state[user_id] = "awaiting_file"
        return await update.message.reply_text("Send me the file you want to upload.")

    elif text == "Run Command":
        user_state[user_id] = "awaiting_command"
        return await update.message.reply_text("Send the terminal command to run.")

    elif user_state.get(user_id) == "awaiting_command":
        cmd = text
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=10)
            result = output.decode()
            suffix = "\n\n🟢 PY Running Successfully" if cmd.startswith("python") else "\n\n✅ Command Executed"
        except subprocess.CalledProcessError as e:
            result = e.output.decode()
            suffix = "\n\n❌ Error occurred"
        except Exception as ex:
            result = str(ex)
            suffix = "\n\n❌ Exception occurred"

        await update.message.reply_text(f"`{cmd}`\n\nOutput:\n{result}{suffix}", parse_mode="Markdown")
        user_state[user_id] = "terminal_menu"

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_state.get(user_id) != "awaiting_file":
        return

    document = update.message.document
    if not document:
        return await update.message.reply_text("❌ No file found.")

    file = await document.get_file()
    file_path = os.path.join(UPLOAD_DIR, document.file_name)
    await file.download_to_drive(file_path)

    await update.message.reply_text(f"✅ File saved: {document.file_name}", reply_markup=terminal_menu)
    user_state[user_id] = "terminal_menu"

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
