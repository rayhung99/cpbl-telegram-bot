import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Telegram Token
TOKEN = "<YOUR_BOT_TOKEN>"

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
# Selenium 抓比賽
# -------------------------
def fetch_cpbl_games():
    url = "https://www.cpbl.com.tw"
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=opts)
    games = []
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "game_item"))
        )
        js = """
        function getStatus(el){
            if(el.classList.contains('final')) return '✅ 已結束';
            if(el.classList.contains('live')) return '🔴 進行中';
            if(el.classList.contains('canceled')) return '❌ 取消';
            return '⏰ 未開始';
        }
        const games = [...document.querySelectorAll('.game_item'), ...document.querySelectorAll('.game_canceled')];
        return games.map(g=>{
            const teams = g.querySelectorAll('.team_name');
            const scores = g.querySelectorAll('.score');
            return {
                away_team: teams[0]?.textContent?.trim() || '',
                home_team: teams[1]?.textContent?.trim() || '',
                away_score: scores[0]?.textContent?.trim() || '0',
                home_score: scores[1]?.textContent?.trim() || '0',
                status: getStatus(g),
                inning: g.querySelector('.inning')?.textContent?.trim() || '',
                game_time: g.querySelector('.game_time')?.textContent?.trim() || '',
                game_link: g.querySelector('a')?.href || ''
            };
        });
        """
        games = driver.execute_script(js)
    except Exception as e:
        print("抓取失敗:", e)
    finally:
        driver.quit()
    return games


# -------------------------
# Bot 指令
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "哈囉！⚾\n\n使用以下指令查詢比賽：\n"
    for cmd, team in GAME_TEAMS.items():
        msg += f"/{cmd} - {team}\n"
    await update.message.reply_text(msg)


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
