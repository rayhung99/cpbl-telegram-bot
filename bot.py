from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import os
import re

TOKEN = os.getenv("TOKEN")  # Railway 環境變數裡的 BotFather Token
TEAM_ID = "147333"  # 固定隊伍 ID
API_URL = f"https://www.thesportsdb.com/api/v1/json/123/eventsnext.php?id={TEAM_ID}"

# 英文隊名 → 中文對照
TEAM_NAME_MAP = {
    "CTBC Brothers": "中信兄弟",
    "Uni-President 7-Eleven Lions": "統一7-ELEVEN獅",
    "Rakuten Monkeys": "樂天桃猿",
    "Fubon Guardians": "富邦悍將",
    "Wei Chuan Dragons": "味全龍",
    "TSG Hawks": "台鋼雄鷹"
}

# -------------------------
# 解析 strResult
# -------------------------
def parse_strResult(str_result):
    readable_result = re.sub(r'<br\s*/?>', '\n', str_result)
    readable_result = re.sub(r'&nbsp;', ' ', readable_result)
    teams_data = readable_result.strip().split('\n\n')
    team_results = []

    for t in teams_data:
        lines = t.strip().split('\n')
        if len(lines) >= 2:
            team_name = team_name_map.get(lines[0].strip(), lines[0].strip())
            scores = lines[1].strip()
            hits_errors = ""
            for line in lines[2:]:
                if "Hits" in line or "Errors" in line:
                    hits_errors += line.strip() + "\n"
            hits_errors = hits_errors.strip()
            team_results.append(f"{team_name}\n局分: {scores}\n{hits_errors}")
    return "\n\n".join(team_results)

# /start 指令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("哈囉！輸入 /nextgame 就能查詢下一場比賽 ⚾")

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

            # 使用 strResult 解析局分、安打、失誤
            str_result = event.get("strResult")
            if str_result:
             detailed_info = parse_strResult(str_result)
            else:
             # 若沒有 strResult，就用簡單比分
             home_score = event.get("intHomeScore", "-")
             away_score = event.get("intAwayScore", "-")
             detailed_info = f"{away_score} - {home_score}"



            # 英文轉中文
            home = TEAM_NAME_MAP.get(home, home)
            away = TEAM_NAME_MAP.get(away, away)

            home_score = event.get("intHomeScore")
            away_score = event.get("intAwayScore")

            if home_score is not None and away_score is not None:
                score_msg = f"比分：{away_score} - {home_score}\n"
            else:
                score_msg = ""

            msg = (
                f"日期: {date}\n"
                f"時間: {time}\n"
                f"{away} vs {home}\n"
                f"{detailed_info}\n"
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
