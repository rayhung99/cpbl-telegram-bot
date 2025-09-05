from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import os

TOKEN = os.getenv("TOKEN")  # BotFather Token 環境變數
TEAM_ID = "147333"  # 固定隊伍 ID
API_URL = f"https://www.thesportsdb.com/api/v1/json/123/eventsnext.php?id={TEAM_ID}"

# 英文隊名到中文對照，依之前資料
cpbl_team_map = {
    "CTBC Brothers": "中信兄弟",
    "Uni-President 7-Eleven Lions": "統一7-ELEVEN獅",
    "Rakuten Monkeys": "樂天桃猿",
    "Fubon Guardians": "富邦悍將",
    "Wei Chuan Dragons": "味全龍",
    "TSG Hawks": "台鋼雄鷹",
}

def to_zh(team_en: str) -> str:
    return cpbl_team_map.get(team_en, team_en)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("哈囉！輸入 /nextgame 就能查詢下一場比賽 ⚽")

async def next_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(API_URL)
        data = response.json()

        if data and "events" in data and isinstance(data["events"], list) and len(data["events"]) > 0:
            event = data["events"]
            if isinstance(event, dict):
                home_en = event.get("strHomeTeam", "未知")
                away_en = event.get("strAwayTeam", "未知")
                date = event.get("dateEventLocal", "未知")
                time = event.get("strTimeLocal", "未知")
                home_score = event.get("intHomeScore")
                away_score = event.get("intAwayScore")

                home = to_zh(home_en)
                away = to_zh(away_en)

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
                msg = "資料格式錯誤，找不到正確比賽事件"
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
