import asyncio
import html
import feedparser
from telegram import Bot
from aiohttp import web

TELEGRAM_TOKEN = "8953657931:AAHiJknl8lm08CaU82NyZZN_HAeFw3iAaU4"
CHAT_ID = "5463779"

EBAY_DOMAINS = [
    ("IT", "https://www.ebay.it"),
    ("DE", "https://www.ebay.de"),
    ("FR", "https://www.ebay.fr"),
    ("UK", "https://www.ebay.co.uk"),
]

KEYWORDS = [
    # Svuota-soffitta & Occasioni
    "svuoto soffitta giochi",
    "svuoto cantina nintendo",
    "vecchi giochi nintendo",
    "cassette nintendo",
    "cassette super nintendo",
    "giochi anni 90",
    "blocco videogiochi vecchi",
    "lotto videogiochi infanzia",
    "scatola vecchi giochi",

    # Distribuzione e Rarità
    "pal gig",
    "distribuzione gig",
    "mattel nes",
    "black label ps1",
    "snes cib",
    "n64 cib",
    "game boy cib",
    "snes ovp",
    "n64 ovp",
    "sigillato nintendo",
    "sealed snes",
    "sealed n64",

    # Console 5ª Gen
    "sega saturn console",
    "sega saturn pal",
    "playstation 1 scatola",
    "ps1 console box",
    "nintendo 64 console",
    "nintendo 64 scatola",
    "3do interactive",
    "atari jaguar console",
    "amiga cd32",
    "pc-fx console",
    "bandai pippin",

    # Console 4ª Gen
    "super nintendo console",
    "snes console scatola",
    "super famicom box",
    "sega mega drive console",
    "sega mega cd",
    "sega 32x console",
    "pc engine console",
    "turbografx 16",
    "neo geo aes console",
    "neo geo cd",
    "philips cd-i",
    "commodore cdtv",

    # Console 3ª Gen & Retro
    "nintendo nes console",
    "nes scatola pal",
    "famicom disk system",
    "sega master system console",
    "atari 2600 console",
    "atari 5200",
    "intellivision console",
    "colecovision",
    "vectrex console",
    "magnavox odyssey",

    # Portatili
    "game boy classic scatola",
    "game boy color box",
    "game boy advance box",
    "game boy micro",
    "virtual boy console",
    "sega game gear console",
    "sega nomad",
    "atari lynx console",
    "neo geo pocket color",
    "wonderswan color",
    "game & watch nintendo",

    # Giochi Rari
    "panzer dragoon saga",
    "shining force 3 saturn",
    "deep fear saturn",
    "snatcher sega mega cd",
    "darxide 32x",
    "alien soldier mega drive",
    "suikoden 2 pal ita",
    "castlevania symphony of the night pal",
    "tombi ps1 pal ita",
    "tombi 2 ps1",
    "klonoa door to phantomile ps1",
    "kula world ps1",
    "silent hill ps1 pal ita",
    "conker bad fur day pal",
    "paper mario n64 pal ita",
    "mega man x3 snes",
    "hagane snes",
    "demon crest snes",
    "terranigma pal ita",
    "whirlo snes",
    "castlevania vampire kiss snes",
    "sunset riders snes",
    "wild guns snes",
    "super metroid big box",
    "zelda snes pal ita",
    "little samson nes",
    "castlevania 3 nes pal ita",
    "snow bros nes",
    "trip world game boy",
    "pokemon smeraldo box",
    "pokemon cristallo box",

    # Scatole, Manuali & Lotti
    "snes solo scatola",
    "scatola super nintendo",
    "n64 box only",
    "game boy box only",
    "ps1 scatola vuota",
    "manuale istruzioni snes",
    "anleitung nintendo",
    "lotto manuali videogiochi",
    "lotto retrogaming pal ita",
    "fondo magazzino videogiochi",
    "lotto console rotte da testare"
]

BLACKLIST = [
    "repro", "riproduzione", "custom", "copia", "falso", "replica", "fake", 
    "custodia vuota ps4", "custodia vuota ps5", "cover art only", "manuale stampato",
    "reprint", "manuale pdf", "box protector", "custodia protettiva", "salvascatola", 
    "protettore box", "proteggi scatola", "protezione pet", "box plastica", 
    "schutzhülle", "boite de protection", "solo guida", "guida strategica", "poster"
]

visti = set()
bot = Bot(token=TELEGRAM_TOKEN)

async def check_ebay(keyword, domain_name, base_url, is_first_run=False):
    query = keyword.replace(" ", "+")
    rss_url = f"{base_url}/sch/i.html?_nkw={query}&_sop=10&LH_BIN=1&_rss=1"
    
    # Headers per evitare blocchi da eBay
    feed = feedparser.parse(rss_url, request_headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    
    max_items = 1 if is_first_run else 5
    
    for entry in feed.entries[:max_items]:
        item_id = entry.link
        title = entry.title
        title_clean = title.lower()
        
        if item_id in visti:
            continue
        if any(bad_word in title_clean for bad_word in BLACKLIST):
            continue
            
        visti.add(item_id)
        
        tag = "📦 <b>Catalogo Esistente</b>" if is_first_run else "🎯 <b>Nuovo Annuncio</b>"
        safe_title = html.escape(title)
        safe_kw = html.escape(keyword)
        
        message = (
            f"{tag} [{domain_name}]\n\n"
            f"📦 <b>Titolo:</b> {safe_title}\n"
            f"🔍 <b>Filtro:</b> {safe_kw}\n\n"
            f"🔗 <a href='{entry.link}'>Apri su eBay {domain_name}</a>"
        )
        
        try:
            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML")
            await asyncio.sleep(1.5)
        except Exception as e:
            print(f"[ERRORE TELEGRAM]: {e}")

async def scraper_loop():
    try:
        await bot.send_message(chat_id=CHAT_ID, text="🚀 <b>Avvio scansione dell'archivio...</b>", parse_mode="HTML")
    except Exception as e:
        print(f"[ERRORE]: {e}")

    # Scansione iniziale archivio
    for kw in KEYWORDS:
        for domain_name, base_url in EBAY_DOMAINS:
            await check_ebay(kw, domain_name, base_url, is_first_run=True)
            await asyncio.sleep(0.5)

    try:
        await bot.send_message(chat_id=CHAT_ID, text="✅ <b>Scansione archivio completata!</b> In ascolto per i nuovi annunci.", parse_mode="HTML")
    except Exception as e:
        print(f"[ERRORE]: {e}")

    # Ciclo sentinella per nuovi annunci
    while True:
        await asyncio.sleep(120)
        for kw in KEYWORDS:
            for domain_name, base_url in EBAY_DOMAINS:
                await check_ebay(kw, domain_name, base_url, is_first_run=False)
                await asyncio.sleep(1.0)

async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_background_tasks(app):
    app['scraper_task'] = asyncio.create_task(scraper_loop())

async def cleanup_background_tasks(app):
    app['scraper_task'].cancel()
    await app['scraper_task']

def init_app():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    return app

if __name__ == "__main__":
    app = init_app()
    web.run_app(app, host='0.0.0.0', port=8080)
