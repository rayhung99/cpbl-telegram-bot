from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import os
import re

# Railway 環境變數裡的 BotFather Token
TOKEN = os.getenv("TOKEN")

# API URL
API_BASE = "https://www.thesportsdb.com/api/v1/json/123/eventsnext.php?id={team_id}"

# 英文隊名 → 中文對照
TEAM_NAME_MAP = {
    "CTBC Brothers": "中信兄弟",
    "Uni-President 7-Eleven Lions": "統一7-ELEVEN獅",
    "Rakuten Monkeys": "樂天桃猿",
    "Fubon Guardians": "富邦悍將",
    "Wei Chuan Dragons": "味全龍",
    "TSG Hawks": "台鋼雄鷹"
}

# TheSportsDB 隊伍 ID
TEAM_IDS = {
    "game1": "147333",  # 台鋼雄鷹
    "game2": "144298",  # 中信兄弟
    "game3": "144301",  # 統一7-ELEVEN獅
    "game4": "144300",  # 樂天桃猿
    "game5": "144299",  # 富邦悍將
    "game6": "144302",  # 味全龍
}


# -------------------------
# 解析 strResult → 表格
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
            if l.lower().startswith("hits") or l.lower().startswith("h"):
                m = re.search(r"(\d+)", l)
                hits = int(m.group(1)) if m else 0
            elif l.lower().startswith("errors") or l.lower().startswith("e"):
                m = re.search(r"(\d+)", l)
                errors = int(m.group(1)) if m else 0
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
# 指令處理
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "哈囉！⚾\n\n"
        "使用以下指令查詢比賽：\n"
        "/game1 - 台鋼雄鷹\n"
        "/game2 - 中信兄弟\n"
        "/game3 - 統一7-ELEVEN獅\n"
        "/game4 - 樂天桃猿\n"
        "/game5 - 富邦悍將\n"
        "/game6 - 味全龍"
    )
    await update.message.reply_text(msg)


async def game_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text.lstrip("/")  # 例如 "game1"
    team_id = TEAM_IDS.get(command)

    if not team_id:
        await update.message.reply_text("❌ 找不到這支隊伍，請確認指令是否正確")
        return

    api_url = API_BASE.format(team_id=team_id)

    try:
        response = requests.get(api_url)
        data = response.json()

        if data and "events" in data and data["events"]:
            event = data["events"][0]  # 最近一場

            home = TEAM_NAME_MAP.get(event.get("strHomeTeam", "未知"), "未知")
            away = TEAM_NAME_MAP.get(event.get("strAwayTeam", "未知"), "未知")
            date = event.get("dateEventLocal", "未知")
            time = event.get("strTimeLocal", "未知")

            # 分數資訊
            str_result = event.get("strResult")
            if str_result:
                score_table = parse_str_result(str_result)
            else:
                score_table = "尚無比賽結果"

            msg = (
                f"日期: {date}\n"
                f"時間: {time}\n"
                f"{away} vs {home}\n\n"
                f"{score_table}"
            )
        else:
            msg = "目前查不到比賽資訊 😢"

    except Exception as e:
        msg = f"⚠️ 錯誤: {e}"

    await update.message.reply_text(msg)


# -------------------------
# 主程式
# -------------------------
def main():
    app = Application.builder().token(TOKEN).build()

    # 指令註冊
    app.add_handler(CommandHandler("start", start))
    for cmd in TEAM_IDS.keys():
        app.add_handler(CommandHandler(cmd, game_handler))

    print("🚀 Bot 已啟動！")
    app.run_polling()


if __name__ == "__main__":
    main()
