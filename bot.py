from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo  # Python 3.9+

# 1) 基本設定
TOKEN = os.getenv("TOKEN")  # Railway 環境變數裡的 BotFather Token
TEAM_ID = "147333"  # TSG Hawks
API_URL = f"https://www.thesportsdb.com/api/v1/json/123/eventsnext.php?id={TEAM_ID}"

# 2) CPBL 英文→中文 對照表
TEAM_NAME_MAP = {
    "CTBC Brothers": "中信兄弟",
    "Fubon Guardians": "富邦悍將",
    "Rakuten Monkeys": "樂天桃猿",
    "Uni-President 7-Eleven Lions": "統一7-ELEVEn獅",
    "Uni-Lions": "統一7-ELEVEn獅",  # 部分來源以簡稱呈現
    "Wei Chuan Dragons": "味全龍",
    "TSG Hawks": "台鋼雄鷹",
}

# 3) 時區設定（預設台北）
TAIPEI_TZ = ZoneInfo("Asia/Taipei")

def to_local_name(eng: str) -> str:
    """英文隊名轉中文，若無對應則回傳原字串。"""
    if not eng:
        return "未知"
    return TEAM_NAME_MAP.get(eng, eng)

def parse_event_local_dt(event: dict) -> datetime | None:
    """
    將 TheSportsDB 事件時間轉為台北時間：
    - 優先使用 strTimestamp（UTC ISO8601）
    - 後備使用 dateEvent + strTime（視為 UTC）
    """
    ts = event.get("strTimestamp")
    if ts:
        try:
            dt_utc = datetime.fromisoformat(ts)
            if dt_utc.tzinfo is None:
                dt_utc = dt_utc.replace(tzinfo=timezone.utc)
            return dt_utc.astimezone(TAIPEI_TZ)
        except Exception:
            pass

    date_str = event.get("dateEvent")
    time_str = event.get("strTime") or event.get("strTimeLocal")
    if date_str and time_str:
        try:
            dt_utc = datetime.fromisoformat(f"{date_str}T{time_str}+00:00")
            return dt_utc.astimezone(TAIPEI_TZ)
        except Exception:
            pass

    # 最後備用：如果 API 直接給了本地日期與時間（不保證一致性）
    date_local = event.get("dateEventLocal")
    time_local = event.get("strTimeLocal")
    if date_local and time_local:
        try:
            # 假設 Local 是台北時間（若來源不一致，建議仍以 UTC 欄位為準）
            dt_local = datetime.fromisoformat(f"{date_local}T{time_local}")
            if dt_local.tzinfo is None:
                dt_local = dt_local.replace(tzinfo=TAIPEI_TZ)
            return dt_local
        except Exception:
            pass

    return None

# 4) /start 指令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("哈囉！輸入 /nextgame 就能查詢下一場比賽 🧢")

# 5) /nextgame 指令 → 查詢 API 並輸出中文隊名＋本地時間
async def next_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and "events" in data and data["events"]:
            event = data["events"]  # 只取最近一場

            home_en = event.get("strHomeTeam", "未知")
            away_en = event.get("strAwayTeam", "未知")
            home = to_local_name(home_en)
            away = to_local_name(away_en)

            # 轉換本地時間
            local_dt = parse_event_local_dt(event)
            if local_dt:
                date_local = local_dt.strftime("%Y-%m-%d")
                time_local = local_dt.strftime("%H:%M")
                tz_name = "台北時間"
            else:
                # 退化顯示：使用回傳的本地欄位或 UTC 欄位並明示
                date_local = event.get("dateEventLocal") or event.get("dateEvent") or "未知"
                time_local = event.get("strTimeLocal") or event.get("strTime") or "未知"
                tz_name = "本地/UTC未明"

            # 分數（TheSportsDB 多為字串或 None）
            home_score = event.get("intHomeScore")
            away_score = event.get("intAwayScore")
            score_msg = ""
            if home_score is not None and away_score is not None:
                score_msg = f"🏆 比分：{home_score} - {away_score}\n"

            msg = (
                "📅 比賽資訊\n\n"
                f"🏟 對戰：{home} vs {away}\n"
                f"{score_msg}"
                f"🗓 日期：{date_local}\n"
                f"⏰ 時間：{time_local}（{tz_name}）"
            )
        else:
            msg = "目前查不到下一場比賽資訊 😢"
    except Exception as e:
        msg = f"⚠️ 錯誤：{e}"

    await update.message.reply_text(msg)

# 6) 進入點
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("nextgame", next_game))
    print("🚀 Bot 已啟動！")
    app.run_polling()

if __name__ == "__main__":
    main()
