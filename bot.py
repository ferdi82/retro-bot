import html
import time
import urllib.request
import urllib.parse
import urllib.error
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import feedparser

TELEGRAM_TOKEN = "8953657931:AAHiJknl8lm08CaU82NyZZN_HAeFw3iAaU4"
CHAT_ID = "5463779"

EBAY_DOMAINS = [
    ("IT", "https://www.ebay.it"),
    ("DE", "https://www.ebay.de"),
    ("FR", "https://www.ebay.fr"),
    ("UK", "https://www.ebay.co.uk"),
]

KEYWORDS = [
    # ==================== SVUOTA-SOFFITTA / OCCASIONI ====================
    "svuoto soffitta giochi",
    "svuoto cantina nintendo",
    "vecchi giochi nintendo",
    "cassette nintendo",
    "cassette super nintendo",
    "giochi anni 90",
    "blocco videogiochi vecchi",
    "lotto videogiochi infanzia",
    "scatola vecchi giochi",

    # ==================== DISTRIBUZIONE & COLLEZIONISMO ====================
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

    # ==================== CONSOLE (32/64 BIT - 5ª GEN) ====================
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

    # ==================== CONSOLE (16 BIT - 4ª GEN) ====================
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

    # ==================== CONSOLE (8 BIT - 3ª GEN) ====================
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

    # ==================== CONSOLE (1ª & 2ª GEN) ====================
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

def send_telegram(message_html):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": "false"
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read()
    except Exception as e:
        print(f"[ERRORE TELEGRAM]: {e}")

def fetch_feed(raw_url):
    # Proxy Bridge per superare il blocco 403 dei server cloud
    encoded_url = urllib.parse.quote(raw_url)
    proxy_urls = [
        f"https://api.allorigins.win/raw?url={encoded_url}",
        f"https://api.codetabs.com/v1/proxy?quest={encoded_url}"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    for p_url in proxy_urls:
        try:
            req = urllib.request.Request(p_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read()
                feed = feedparser.parse(content)
                if feed and getattr(feed, 'entries', None) and len(feed.entries) > 0:
                    return 200, feed
        except Exception:
            continue

    return "Proxy Blocked", None

def check_ebay(keyword, domain_name, base_url, is_first_run=False):
    query = urllib.parse.quote_plus(keyword)
    rss_url = f"{base_url}/sch/i.html?_nkw={query}&_sop=10&LH_BIN=1&_rss=1"
    
    status, feed = fetch_feed(rss_url)
    
    if feed is None or not getattr(feed, 'entries', None):
        return status, 0

    inviati = 0
    max_items = 1 if is_first_run else 4
    
    for entry in feed.entries[:max_items]:
        item_id = getattr(entry, 'link', '')
        title = getattr(entry, 'title', '')
        if not item_id or not title:
            continue

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
            f"🔗 <a href='{item_id}'>Apri su eBay {domain_name}</a>"
        )
        
        send_telegram(message)
        inviati += 1
        time.sleep(1.2)
        
    return status, inviati

class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        return

def run_web_server():
    server = HTTPServer(('0.0.0.0', 8080), PingHandler)
    server.serve_forever()

def main():
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()

    time.sleep(2)
    send_telegram("🚀 <b>Test di Connessione con Proxy Bridge...</b>")

    test_status, test_found = check_ebay("game boy console", "IT", "https://www.ebay.it", is_first_run=True)
    send_telegram(f"🔍 <b>Diagnostica eBay (via Proxy):</b>\n- Risposta: <code>{test_status}</code>\n- Annunci scaricati: <code>{test_found}</code>")

    # 1. Scansione archivio esistente
    for kw in KEYWORDS:
        for domain_name, base_url in EBAY_DOMAINS:
            check_ebay(kw, domain_name, base_url, is_first_run=True)
            time.sleep(0.5)

    send_telegram("✅ <b>Base pronta!</b> Da ora in avanti riceverai solo i nuovi annunci pubblicati.")

    # 2. Monitoraggio continuo
    while True:
        time.sleep(60)
        for kw in KEYWORDS:
            for domain_name, base_url in EBAY_DOMAINS:
                check_ebay(kw, domain_name, base_url, is_first_run=False)
                time.sleep(0.8)

if __name__ == "__main__":
    main()
