import asyncio
import feedparser
from telegram import Bot
from aiohttp import web

TELEGRAM_TOKEN = "8953657931:AAHiJknl8lm08CaU82NyZZN_HAeFw3iAaU4"
CHAT_ID = "5463779"

KEYWORDS = [
    "snes solo scatola",
    "scatola super nintendo",
    "manuale snes",
    "super metroid snes",
    "zelda snes pal ita",
    "lotto giochi snes",
    "lotto manuali nintendo"
]

BLACKLIST = ["repro", "riproduzione", "custom", "copia", "falso", "replica", "fake"]

visti = set()
bot = Bot(token=TELEGRAM_TOKEN)

async def check_ebay(keyword):
    query = keyword.replace(" ", "+")
    rss_url = f"https://www.ebay.it/sch/i.html?_nkw={query}&_sop=10&_rss=1"
    
    feed = feedparser.parse(rss_url)
    
    for entry in feed.entries[:5]:
        item_id = entry.link
        title_clean = entry.title.lower()
        
        if item_id in visti:
            continue
        if any(bad_word in title_clean for bad_word in BLACKLIST):
            continue
            
        visti.add(item_id)
        
        message = (
            f"🎯 *Nuovo Affare Rilevato!*\n\n"
            f"📦 *Titolo:* {entry.title}\n"
            f"🔍 *Filtro:* {keyword}\n\n"
            f"🔗 [Apri l'annuncio su eBay]({entry.link})"
        )
        
        try:
            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
            print(f"[OK] Inviato: {entry.title}")
        except Exception as e:
            print(f"[ERRORE]: {e}")

async def scraper_loop():
    while True:
        for kw in KEYWORDS:
            await check_ebay(kw)
            await asyncio.sleep(2)
        await asyncio.sleep(180)

async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def main():
    asyncio.create_task(scraper_loop())
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
  
