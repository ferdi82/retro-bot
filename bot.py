import asyncio
import feedparser
from telegram import Bot
from aiohttp import web

TELEGRAM_TOKEN = "8953657931:AAHiJknl8lm08CaU82NyZZN_HAeFw3iAaU4"
CHAT_ID = "5463779"

KEYWORDS = [
    # 5ª Generazione (32/64-bit)
    "sega saturn",
    "playstation 1 scatola",
    "ps1 pal ita",
    "nintendo 64 scatola",
    "nintendo 64 giochi",
    "3do interactive",
    "atari jaguar",
    "amiga cd32",
    "pc-fx console",
    "bandai pippin",
    
    # 4ª Generazione (16-bit)
    "snes solo scatola",
    "scatola super nintendo",
    "manuale snes",
    "super metroid snes",
    "zelda snes pal ita",
    "sega mega drive",
    "sega mega cd",
    "sega 32x",
    "pc engine",
    "turbografx",
    "neo geo aes",
    "neo geo cd",
    "philips cd-i",
    "commodore cdtv",
    
    # 3ª Generazione (8-bit)
    "nintendo nes scatola",
    "nes pal ita",
    "famicom disk system",
    "sega master system",
    "sega sg-1000",
    "atari 7800",
    "atari xegs",
    "amstrad gx4000",
    "commodore 64gs",
    
    # 1ª e 2ª Generazione & Retrogaming Storico
    "atari 2600",
    "atari 5200",
    "intellivision",
    "colecovision",
    "vectrex",
    "magnavox odyssey",
    "videopac g7000",
    
    # Portatili Storici
    "game boy scatola",
    "game boy advance box",
    "virtual boy",
    "sega game gear",
    "sega nomad",
    "atari lynx",
    "neo geo pocket",
    "wonderswan",
    "game & watch nintendo",
    
    # Lotti e Ricerche Generiche
    "lotto retrogaming",
    "lotto giochi nintendo",
    "lotto manuali nintendo",
    "lotto console rotte da testare",
    "stock videogiochi vecchi"
]

BLACKLIST = [
    "repro", "riproduzione", "custom", "copia", "falso", "replica", "fake", 
    "custodia vuota", "cover art", "box art only"
]

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
