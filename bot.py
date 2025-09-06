from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import os
import re

TOKEN = os.getenv("TOKEN")  # Railway 環境變數
API_BASE = "https://www.thesportsdb.com/api/v1/json/123/eventsnext.php?id={team_id}"

# 英文隊名 → 中文
TEAM_NAME_MAP = {
    "CTBC Brothers": "中信兄弟",
    "Uni-President 7-Eleven Lions": "統一7-ELEVEN獅",
    "Rakuten Monkeys": "樂天桃猿",
    "Fubon Guardians": "富邦悍將",
    "Wei Chuan Dragons": "味全龍",
    "TSG Hawks": "台鋼雄鷹"
}

# 隊伍 ID
TEAM_IDS = {
    "CTBC Brothers": "144298",
    "Uni-President 7-Eleven Lions": "144301",
    "Rakuten Monkeys": "144300",
    "Fubon Guardians": "144299",
    "Wei Chuan Dragons": "144302",
    "TSG Hawks": "147333"
}

# gameX 對應表
GAME_COMMANDS = {
    "game1": "TSG Hawks",
    "game2": "CTBC Brothers",
    "game3": "Uni-President 7-Eleven Lions",
    "game4": "Rakuten Monkeys",
    "game5": "Fubon Guardians",
    "game6": "Wei Chuan Dragons"
}


# -------------------------
# 解析比賽結果
# -------------------------
def parse_str_result(str_result: str) -> str:
    # HTML 清理
    readable = re.sub(r'<br\s*/?>', '\n', str_result)
    readable = re.sub(r'&nbsp;', ' ', readable)

    blocks = [b.strip() for b in readable.strip().split('\n\n') if b.strip()]
    team_data = []

    for block in blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not lines:
            continue

        # 隊伍名稱 (去掉 "Innings:")
        team_name_raw = re.sub(r"\s*Innings:.*$", "", lines[0])
        team_name = TEAM_NAME_MAP.get(team_name_raw, team_name_raw)

        scores = []
        hits = 0
        errors = 0

        for l in lines[1:]:
            if l.startswith("Hits"):
                hits = int(re.search(r"(\d+)", l).group(1))
            elif l.startswith("Errors"):
                errors = int(re.search(r"(\d+)", l).group(1))
            elif re.match(r"^[0-9\s]+$", l):  # 局分數字
                scores = [int(x) for x in l.split() if x.isdigit()]

        # 補滿 9 局
        while len(scores) < 9:
            scores.append("-")

        # 計算總分 R
        runs = sum(s for s in scores if isinstance(s, int))

        team_data.append({
            "name": team_name,
            "scores": scores,
            "R": runs,
            "H": hits,
            "E": errors
        })

    # 總表格式
    header = "1 2 3 4 5 6 7 8 9 | R  H  E"
    lines = [header]
    for t in team_data:
        scores_str = " ".join(str(s) for s in t["scores"])
        line = f"{scores_str} | {t['R']}  {t['H']}  {t['E']}   {t['name']}"
        lines.append(line)

    return "\n".join(lines)


# -------------------------
# Bot 指令
# -------------------------

# /start 指令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "哈囉！⚾\n"
        "以下指令可查詢比賽：\n"
        "/game1 - 台鋼雄鷹\n"
        "/game2 - 中信兄弟\n"
        "/game3 - 統一7-ELEVEN獅\n"
        "/game4 - 樂天桃猿\n"
        "/game5 - 富邦悍將\n"
        "/game6 - 味全龍"
    )


# 查詢指定隊伍比賽
async def fetch_game(update: Update, context: ContextTypes.DEFAULT_TYPE, team_eng: str):
    team_id = TEAM_IDS[team_eng]
    team_zh = TEAM_NAME_MAP[team_eng]

    try:
        response = requests.get(API_BASE.format(team_id=team_id))
        data = response.json()

        if data and "events" in data and data["events"]:
            event = data["events"][0]

            home = TEAM_NAME_MAP.get(event.get("strHomeTeam", "未知"), event.get("strHomeTeam", "未知"))
            away = TEAM_NAME_MAP.get(event.get("strAwayTeam", "未知"), event.get("strAwayTeam", "未知"))
            date = event.get("dateEventLocal", "未知")
            time = event.get("strTimeLocal", "未知")

            str_result = event.get("strResult")
            if str_result:
                detailed_info = parse_str_result(str_result)
                status = "已結束或進行中"
            else:
                detailed_info = "目前尚無比分資訊"
                status = "尚未開打"

            msg = (
                f"隊伍: {team_zh}\n"
                f"日期: {date}\n"
                f"時間: {time}\n"
                f"狀態: {status}\n"
                f"{away} vs {home}\n\n"
                f"{detailed_info}"
            )
        else:
            msg = "目前查不到比賽資訊 😢"

    except Exception as e:
        msg = f"⚠️ 錯誤: {e}"

    await update.message.reply_text(msg)


# 建立 /gameX handler
def add_game_handlers(app):
    for cmd, team_eng in GAME_COMMANDS.items():
        async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE, team=team_eng):
            await fetch_game(update, context, team)
        app.add_handler(CommandHandler(cmd, handler))


# -------------------------
# 主程式
# -------------------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    add_game_handlers(app)

    print("🚀 Bot 已啟動！")
    app.run_polling()


if __name__ == "__main__":
    main()
