from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
import sys

TOKEN = os.getenv("TOKEN")  # 從 Railway 環境變數讀取

if not TOKEN:
    print("❌ 錯誤：沒有讀到 TOKEN 環境變數！請確認 Railway → Variables 已設定 TOKEN。")
    sys.exit(1)
else:
    print("✅ 成功讀到 TOKEN（前10碼）:", TOKEN[:10] + "********")

# /start 指令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("哈囉！我是你的 Telegram Bot 🤖")

# 一般文字訊息
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("🚀 Bot 已啟動！等待訊息中...")
    app.run_polling()

if __name__ == "__main__":
    main()
