from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import os
import re

TOKEN = os.getenv("TOKEN")  # BotFather Token
API_BASE = "https://www.thesportsdb.com/api/v1/json/123/eventsnext.php?id="

# 英文隊名 → 中文對照
TEAM_NAME_MAP = {
    "CTBC Brothers": "中信兄弟",
    "Uni-President 7-Eleven Lions": "統一7-ELEVEN獅",
    "Rakuten Monkeys": "樂天桃猿",
    "Fubon Guardians": "富邦悍將",
    "Wei Chuan Dragons": "味全龍",
    "TSG Hawks": "台鋼雄鷹"
}

TEAM_IDS = {
    "CTBC Brothers": "144298",
    "Uni-President 7-Eleven Lions": "144301",
    "Rakuten Monkeys": "144300",
    "Fubon Guardians": "144299",
    "Wei Chuan Dragons": "144302",
    "TSG Hawks": "147333"
}

# -------------------------
# 解析 strResult
# -------------------------
def parse_str_result(str_result: str) -> str:
    readable = re.sub(r'<br\s*/?>', '\n', str_result)
    readable = re.sub(r'&nbsp;', ' ', readable)
    blocks = [b.strip() for b in readable.strip().split('\n\n') if b.strip()]
    results = []

    for block in blocks:
        lines = block.split('\n')
        if len(lines) < 2:
            continue
        team_name = TEAM_NAME_MAP.get(lines[0].strip(), lines[0].strip())
        scores = lines[1].strip()
        hits_errors = "\n".join(l.strip() for l in lines[2:] if "Hits" in l or "Errors" in l)
        results.append(f"{team_name}\n局分: {scores}\n{hits_errors}".strip())

    return "\n\n".join(results)

# /start 指令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "哈囉！輸入 /nextgame <隊伍英文名> 查詢下一場比賽 ⚾\n"
        "可查詢隊伍: " + ", ".join(TEAM_NAME_MAP.keys())
    )

# /nextgame 指令
async def next_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("請輸入隊伍英文名稱，例如：/nextgame CTBC Brothers")
            return

        team_name = " ".join(context.args)
        team_id = TEAM_IDS.get(team_name)
        if not team_id:
            await update.message.reply_text("找不到該隊伍，請確認英文名稱是否正確。")
            return

        response = requests.get(API_BASE + team_id, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("events"):
            await update.message.reply_text("目前查不到下一場比賽資訊 😢")
            return

        event = data["events"][0]  # 最近一場
        home = TEAM_NAME_MAP.get(event.get("strHomeTeam", "未知"), event.get("strHomeTeam", "未知"))
        away = TEAM_NAME_MAP.get(event.get("strAwayTeam", "未知"), event.get("strAwayTeam", "未知"))
        date = event.get("dateEventLocal", "未知")
        time = event.get("strTimeLocal", "未知")
        str_result = event.get("strResult")

        # 判斷比賽狀態
        if not str_result:
            status = "尚未開打"
            score_info = f"{away} vs {home}"
        else:
            status = "已結束或進行中"
            score_info = parse_str_result(str_result)

        msg = (
            f"隊伍: {team_name}\n"
            f"日期: {date}\n"
            f"時間: {time}\n"
            f"狀態: {status}\n"
            f"{score_info}"
        )

    except Exception as e:
        msg = f"⚠️ 發生錯誤: {e}"

    await update.message.reply_text(msg)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("nextgame", next_game))

    print("🚀 Bot 已啟動！")
    app.run_polling()

if __name__ == "__main__":
    main()
