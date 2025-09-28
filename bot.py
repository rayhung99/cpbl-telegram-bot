import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from playwright.sync_api import sync_playwright

# -------------------------
# Telegram Token
# -------------------------
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("❌ Telegram Token 未設定，請在 Railway 環境變數中設定 TOKEN")

# gameX 對應隊伍
GAME_TEAMS = {
    "game1": "台鋼雄鷹",
    "game2": "中信兄弟",
    "game3": "統一7-ELEVEN獅",
    "game4": "樂天桃猿",
    "game5": "富邦悍將",
    "game6": "味全龍"
}

# -------------------------
# Playwright 抓比賽
# -------------------------
def fetch_cpbl_games():
    url = "https://www.cpbl.com.tw"
    games = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=15000)
        try:
            games = page.eval_on_selector_all(
                ".game_item, .game_canceled",
                """
                (games) => games.map(g => {
                    const teams = g.querySelectorAll('.team_name');
                    const scores = g.querySelectorAll('.score');
                    const status = g.className.includes('final') ? '✅ 已結束' :
                                   g.className.includes('live') ? '🔴 進行中' :
                                   g.className.includes('canceled') ? '❌ 取消' :
                                   '⏰ 未開始';
                    return {
                        away_team: teams[0]?.textContent?.trim() || '',
                        home_team: teams[1]?.textContent?.trim() || '',
                        away_score: scores[0]?.textContent?.trim() || '0',
                        home_score: scores[1]?.textContent?.trim() || '0',
                        status: status,
                        game_link: g.querySelector('a')?.href || ''
                    };
                })
                """
            )
        except Exception as e:
            print("抓取失敗:", e)
        browser.close()
    return games

# -------------------------
# /start 指令
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "哈囉！⚾\n\n使用以下指令查詢比賽：\n"
    for cmd, team in GAME_TEAMS.items():
        msg += f"/{cmd} - {team}\n"
    await update.message.reply_text(msg)

# -------------------------
# /gameX 指令
# -------------------------
async def game_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text.lstrip("/")
    team_name = GAME_TEAMS.get(command)
    if not team_name:
        await update.message.reply_text("❌ 找不到這支隊伍")
        return

    await update.message.reply_text("⏳ 正在抓取比賽資料，請稍候…")

    games = fetch_cpbl_games()
    if not games:
        await update.message.reply_text("⚠️ 無法取得比賽資料")
        return

    # 找指定隊伍的比賽
    for game in games:
        if team_name in [game.get("home_team"), game.get("away_team")]:
            away = game.get("away_team", "")
            home = game.get("home_team", "")
            status = game.get("status", "")
            link = game.get("game_link", "")
            msg = (
                f"{away} vs {home}\n"
                f"狀態: {status}\n"
                f"連結: {link}\n\n"
                f"比分: {game.get('away_score')} - {game.get('home_score')}"
            )
            await update.message.reply_text(msg)
            return

    await update.message.reply_text("今天沒有這支隊伍的比賽 😢")

# -------------------------
# 主程式
# -------------------------
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    for cmd in GAME_TEAMS.keys():
        app.add_handler(CommandHandler(cmd, game_handler))

    print("🚀 Bot 已啟動！")
    app.run_polling()

if __name__ == "__main__":
    main()
