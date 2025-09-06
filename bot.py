from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import os
import re

TOKEN = os.getenv("TOKEN")  # BotFather Token
API_BASE = "https://www.thesportsdb.com/api/v1/json/123/eventsnext.php?id="

# 隊伍資料 (ID + 中文名)
TEAMS = {
    "game1": {"id": "147333", "name": "台鋼雄鷹"},
    "game2": {"id": "144298", "name": "中信兄弟"},
    "game3": {"id": "144301", "name": "統一7-ELEVEN獅"},
    "game4": {"id": "144300", "name": "樂天桃猿"},
    "game5": {"id": "144299", "name": "富邦悍將"},
    "game6": {"id": "144302", "name": "味全龍"},
}

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
        hits_errors = "\n".join(
            l.strip() for l in lines[2:] if "Hits" in l or "Errors" in l
        )
        results.append(f"{team_name}\n局分: {scores}\n{hits_errors}".strip())

    return "\n\n".join(results)

# 查詢比賽資訊
async def fetch_next_game(team_key: str) -> str:
    try:
        team = TEAMS[team_key]
        team_id, team_name = team["id"], team["name"]

        response = requests.get(API_BASE + team_id, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("events"):
            return f"{team_name} 目前查不到下一場比賽資訊 😢"

        event = data["events"][0]
        home = TEAM_NAME_MAP.get(event.get("strHomeTeam", "未知"), event.get("strHomeTeam", "未知"))
        away = TEAM_NAME_MAP.get(event.get("strAwayTeam", "未知"), event.get("strAwayTeam", "未知"))
        date = event.get("dateEventLocal", "未知")
        time = event.get("strTimeLocal", "未知")
        str_result = event.get("strResult")

        if not str_result:
            status = "尚未開打"
            score_info = f"{away} vs {home}"
        else:
            status = "已結束或進行中"
            score_info = parse_str_result(str_result)

        return (
            f"隊伍: {team_name}\n"
            f"日期: {date}\n"
            f"時間: {time}\n"
            f"狀態: {status}\n"
            f"{score_info}"
        )

    except Exception as e:
        return f"⚠️ 發生錯誤: {e}"

# 單隊指令
async def game1(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(await fetch_next_game("game1"))
async def game2(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(await fetch_next_game("game2"))
async def game3(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(await fetch_next_game("game3"))
async def game4(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(await fetch_next_game("game4"))
async def game5(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(await fetch_next_game("game5"))
async def game6(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text(await fetch_next_game("game6"))

# 全部隊伍指令
async def allgames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages = []
    for key in TEAMS.keys():
        result = await fetch_next_game(key)
        messages.append(result)
    await update.message.reply_text("\n\n---\n\n".join(messages))

def main():
    app = Application.builder().token(TOKEN).build()

    # 註冊單隊指令
    app.add_handler(CommandHandler("game1", game1))
    app.add_handler(CommandHandler("game2", game2))
    app.add_handler(CommandHandler("game3", game3))
    app.add_handler(CommandHandler("game4", game4))
    app.add_handler(CommandHandler("game5", game5))
    app.add_handler(CommandHandler("game6", game6))

    # 註冊全部隊伍
    app.add_handler(CommandHandler("allgames", allgames))

    print("🚀 Bot 已啟動！")
    app.run_polling()

if __name__ == "__main__":
    main()
