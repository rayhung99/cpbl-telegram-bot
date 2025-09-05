from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import os

TOKEN = os.getenv("TOKEN")  # Railway 環境變數裡的 BotFather Token
TEAM_ID = "147333"  # 固定隊伍 ID
API_URL = f"https://www.thesportsdb.com/api/v1/json/123/eventsnext.php?id={TEAM_ID}"

# /start 指令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("哈囉！輸入 /nextgame 就能查詢下一場比賽 ⚽")

# /nextgame 指令 → 查詢 API
async def next_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(API_URL)
        data = response.json()

        if data and "events" in data and data["events"]:
            event = data["events"][0]  # 只取最近一場

            home = event.get("strHomeTeam", "未知")
            away = event.get("strAwayTeam", "未知")
            date = event.get("dateEventLocal", "未知")
            time = event.get("strTimeLocal", "未知")

            home_score = event.get("intHomeScore")
            away_score = event.get("intAwayScore")

            if home_score is not None and away_score is not None:
                score_msg = f"比分：{away_score} - {home_score}\n"
            else:
                score_msg = ""

            msg = (
                f"日期: {date}\n"
                f"時間: {time} (UTC)\n"
                f"{away} vs {home}\n"
                f"{score_msg}"

            )
        else:
            msg = "目前查不到下一場比賽資訊 😢"

    except Exception as e:
        msg = f"⚠️ 錯誤: {e}"

    await update.message.reply_text(msg)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("nextgame", next_game))

    print("🚀 Bot 已啟動！")
    app.run_polling()

if __name__ == "__main__":
    main()
