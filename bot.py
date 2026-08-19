import asyncio
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
    # ==================== SVUOTA-SOFFITTA / OCCASIONI INCONSAPEVOLI ====================
    "svuoto soffitta giochi",
    "svuoto cantina nintendo",
    "vecchi giochi nintendo",
    "cassette nintendo",
    "cassette super nintendo",
    "giochi anni 90",
    "blocco videogiochi vecchi",
    "lotto videogiochi infanzia",
    "scatola vecchi giochi",

    # ==================== DISTRIBUZIONE ITALIANA & TERMINI COLLEZIONISTICI ====================
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

    # ==================== CONSOLE (5ª GEN - 32/64 BIT) ====================
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
    "casio loopy",
    "bandai playdia",

    # ==================== CONSOLE (4ª GEN - 16 BIT) ====================
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
    "pioneer laseractive",

    # ==================== CONSOLE (3ª GEN - 8 BIT) ====================
    "nintendo nes console",
    "nes scatola pal",
    "famicom disk system",
    "sega master system console",
    "sega sg-1000",
    "atari 7800",
    "atari xegs",
    "amstrad gx4000",
    "commodore 64gs",
    "epoch cassette vision",

    # ==================== CONSOLE (1ª & 2ª GEN - RETRO STORICO) ====================
    "atari 2600 console",
    "atari 5200",
    "intellivision console",
    "colecovision",
    "vectrex console",
    "magnavox odyssey",
    "videopac g7000",
    "fairchild channel f",
    "creativision vtech",

    # ==================== CONSOLE PORTATILI ====================
    "game boy classic scatola",
    "game boy color box",
    "game boy advance box",
    "game boy micro",
    "virtual boy console",
    "sega game gear console",
    "sega nomad",
    "atari lynx console",
    "turboexpress",
    "neo geo pocket color",
    "wonderswan color",
    "game & watch nintendo",
    "watara supervision",

    # ==================== GIOCHI RARI SEGA ====================
    "panzer dragoon saga",
    "shining force 3 saturn",
    "deep fear saturn",
    "keio flying squadron",
    "burning rangers saturn",
    "radiant silvergun",
    "snatcher sega mega cd",
    "knuckles chaotix 32x",
    "darxide 32x",
    "alien soldier mega drive",
    "the punisher mega drive",
    "mega man wily wars",
    "castlevania new generation",
    "smurfs travel world master system",

    # ==================== GIOCHI RARI PLAYSTATION 1 ====================
    "suikoden 2 pal ita",
    "castlevania symphony of the night pal",
    "tombi ps1 pal ita",
    "tombi 2 ps1",
    "klonoa door to phantomile ps1",
    "kula world ps1",
    "mega man legends ps1",
    "clock tower ps1",
    "in the hunt ps1",
    "silent hill ps1 pal ita",
    "resident evil ps1 big box",

    # ==================== GIOCHI RARI NINTENDO 64 ====================
    "conker bad fur day pal",
    "paper mario n64 pal ita",
    "mario party 3 n64",
    "castlevania legacy darkness n64",
    "snowboard kids 2 n64",
    "stunt racer 64",
    "worms armageddon n64",
    "resident evil 2 n64 pal ita",

    # ==================== GIOCHI RARI SNES ====================
    "mega man x3 snes",
    "mega man 7 snes",
    "hagane snes",
    "demon crest snes",
    "terranigma pal ita",
    "whirlo snes",
    "castlevania vampire kiss snes",
    "sunset riders snes pal",
    "wild guns snes",
    "secret of evermore pal ita",
    "illusion of time pal ita",
    "lufia 2 pal ita",
    "super metroid big box",
    "zelda snes pal ita",

    # ==================== GIOCHI RARI NES ====================
    "little samson nes",
    "flintstones dinosaur nes",
    "castlevania 3 nes pal ita",
    "duck tales 2 nes",
    "snow bros nes",
    "panic restaurant nes",
    "bubble bobble 2 nes",
    "mega man nes pal ita",
    "stadium events nes",

    # ==================== GIOCHI RARI PORTATILI ====================
    "trip world game boy",
    "pokemon smeraldo box pal ita",
    "pokemon cristallo box pal ita",
    "pokemon rosso fuoco box",
    "pokemon foglia verde box",
    "ninja cop gba",
    "boktai pal ita",
    "castlevania aria sorrow pal ita",
    "shantae gbc",
    "metal gear solid gbc",

    # ==================== GIOCHI RARI NEO GEO & ALTRI ====================
    "neo geo aes game",
    "twinkle star sprites aes",
    "metal slug neo geo",
    "castlevania rondo blood pc engine",
    "magical chase pc engine",
    "alien vs predator jaguar",
    "battlesphere jaguar",

    # ==================== SCATOLE, MANUALI, LOTTI & FONDI ====================
    "snes solo scatola",
    "scatola super nintendo",
    "n64 box only",
    "game boy box only",
    "ps1 scatola vuota",
    "manuale istruzioni snes",
    "anleitung nintendo",
    "boite snes sans jeu",
    "lotto manuali videogiochi",
    "lotto manuali nintendo",
    "lotto retrogaming pal ita",
    "fondo magazzino videogiochi",
    "deadstock videogiochi",
    "lotto console rotte da testare",
    "stock videogiochi vecchi"
]

BLACKLIST = [
    "repro", "riproduzione", "custom", "copia", "falso", "replica", "fake", 
    "custodia vuota ps4", "custodia vuota ps5", "cover art only", "manuale stampato",
    "reprint", "manuale pdf",
    "box protector", "custodia protettiva", "salvascatola", "protettore box",
    "proteggi scatola", "protezione pet", "box plastica", "schutzhülle", "boite de protection",
    "solo guida", "guida strategica", "poster", "solo poster", "lösungsbuch"
]

visti = set()
bot = Bot(token=TELEGRAM_TOKEN)

async def check_ebay(keyword, domain_name, base_url, is_first_run=False):
    query = keyword.replace(" ", "+")
    rss_url = f"{base_url}/sch/i.html?_nkw={query}&_sop=10&LH_BIN=1&_rss=1"
    
    feed = feedparser.parse(rss_url)
    
    # Nel primo ciclo prende i primi 2 annunci esistenti per parola chiave; nei successivi fino a 5
    max_items = 2 if is_first_run else 5
    
    for entry in feed.entries[:max_items]:
        item_id = entry.link
        title_clean = entry.title.lower()
        
        if item_id in visti:
            continue
        if any(bad_word in title_clean for bad_word in BLACKLIST):
            continue
            
        visti.add(item_id)
        
        tag = "📦 Catalogo Esistente" if is_first_run else "🎯 Nuovo Annuncio"
        message = (
            f"{tag} *[{domain_name}]*\n\n"
            f"📦 *Titolo:* {entry.title}\n"
            f"🔍 *Filtro:* {keyword}\n\n"
            f"🔗 [Apri su eBay {domain_name}]({entry.link})"
        )
        
        try:
            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
            await asyncio.sleep(2)  # Pausa anti-spam Telegram
        except Exception as e:
            print(f"[ERRORE TELEGRAM]: {e}")

async def scraper_loop():
    try:
        await bot.send_message(chat_id=CHAT_ID, text="🚀 *Avvio scansione dell'archivio esistente su eBay...* (Riceverai i migliori annunci attualmente attivi)")
    except Exception as e:
        print(f"[ERRORE]: {e}")

    # 1. SCANSIONE INIZIALE DI TUTTO L'ESISTENTE
    for kw in KEYWORDS:
        for domain_name, base_url in EBAY_DOMAINS:
            await check_ebay(kw, domain_name, base_url, is_first_run=True)
            await asyncio.sleep(1)

    try:
        await bot.send_message(chat_id=CHAT_ID, text="✅ *Scansione archivio completata!* Da ora in poi riceverai solo i nuovi annunci pubblicati in tempo reale.")
    except Exception as e:
        print(f"[ERRORE]: {e}")

    # 2. CICLO NORMALE PER I SOLI NUOVI ANNUNCI
    while True:
        await asyncio.sleep(120)
        for kw in KEYWORDS:
            for domain_name, base_url in EBAY_DOMAINS:
                await check_ebay(kw, domain_name, base_url, is_first_run=False)
                await asyncio.sleep(1.5)

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
