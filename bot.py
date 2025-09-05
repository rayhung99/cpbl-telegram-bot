# cpbl_bot.py
# 功能：查詢比賽並將英文隊名自動轉換為中文（中華職棒六隊）
# 依據：CPBL 官方網站與維基列出的現役六隊中英文名稱對照 [20][2]

import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 1) 英文→中文 隊名映射（中華職棒六隊）
# 來源：CPBL 官網 Teams、維基現役球團表 [20][2]
cpbl_team_map = {
    "CTBC Brothers": "中信兄弟",                 # [20][2]
    "Uni-President 7-Eleven Lions": "統一7-ELEVEN獅",  # [20][2]
    "Rakuten Monkeys": "樂天桃猿",               # [20][2]
    "Fubon Guardians": "富邦悍將",               # [20][2]
    "Wei Chuan Dragons": "味全龍",               # [20][2]
    "TSG Hawks": "台鋼雄鷹",                     # [20][2]
}

def to_zh(team_en: str) -> str:
    """將英文隊名轉為中文；若無對應則回傳原字串。"""
    if not isinstance(team_en, str):
        return team_en
    return cpbl_team_map.get(team_en.strip(), team_en)

# 2) Telegram Bot 設定（請將 TOKEN 設為環境變數）
TOKEN = os.getenv("TOKEN")  # Railway/伺服器環境變數中的 BotFather Token [2]
TEAM_ID = "147333"  # 範例隊伍 ID（TheSportsDB 範例；請依實際需求調整）[2]
API_URL = f"https://www.thesportsdb.com/api/v1/json/123/eventsnext.php?id={TEAM_ID}"  # [2]

# /start 指令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("哈囉！輸入 /nextgame 就能查詢下一場比賽 ⚾")  # [2][20]

# /nextgame 指令：查詢 API 並輸出中文隊名
async def next_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resp = requests.get(API_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data and "events" in data and data["events"]:
            event = data["events"]  # 最近一場 [2]
            home_en = event.get("strHomeTeam", "Unknown")  # [2]
            away_en = event.get("strAwayTeam", "Unknown")  # [2]
            date_local = event.get("dateEventLocal") or event.get("dateEvent") or "未知"  # [2]
            time_local = event.get("strTimeLocal") or event.get("strTime") or "未知"       # [2]
            home_zh = to_zh(home_en)  # 英→中 [20][2]
            away_zh = to_zh(away_en)  # 英→中 [20][2]

            # 分數（若已開打/完賽）
            home_score = event.get("intHomeScore")
            away_score = event.get("intAwayScore")
            score_msg = f"比分：{away_score} - {home_score}\n" if (home_score is not None and away_score is not None) else ""  # [2]

            msg = (
                f"日期：{date_local}\n"
                f"時間：{time_local}（Local）\n"
                f"{away_zh} vs {home_zh}\n"
                f"{score_msg}"
            )  # [2][20]
        else:
            msg = "目前查不到下一場比賽資訊 😢"  # [2]
    except Exception as e:
        msg = f"⚠️ 錯誤: {e}"  # [2]

    await update.message.reply_text(msg)  # [2]

def main():
    app = Application.builder().token(TOKEN).build()  # [2]
    app.add_handler(CommandHandler("start", start))   # [2]
    app.add_handler(CommandHandler("nextgame", next_game))  # [2]
    print("🚀 Bot 已啟動！")  # [2]
    app.run_polling()  # [2]

if __name__ == "__main__":
    main()  # [2]
