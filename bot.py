import html
import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

# Configurazione Telegram
TELEGRAM_TOKEN = "8953657931:AAHiJknl8lm08CaU82NyZZN_HAeFw3iAaU4"
CHAT_ID = "5463779"

# App ID Ufficiale eBay
EBAY_APP_ID = "Ferdinan-Myretrob-PRD-60149ee33-875cf987"

# Marketplace ufficiali (Global ID eBay)
MARKETPLACES = [
    ("IT", "EBAY-IT"),
    ("DE", "EBAY-DE"),
    ("FR", "EBAY-FR"),
    ("GB", "EBAY-GB"),
]

KEYWORDS = [
    # ==================== LOTTI SVUOTA-CANTINA / SOFFITTA / SFUSI (MULTI-LINGUA) ====================
    # Italiano
    "svuoto soffitta giochi nintendo",
    "svuoto cantina nintendo",
    "cassette nintendo vecchie",
    "blocco cassette nintendo",
    "lotto giochi snes",
    "lotto cassette super nintendo",
    "lotto giochi nintendo 64",
    "lotto cassette n64",
    "lotto giochi game boy",
    "lotto cartucce mega drive",
    "stock videogiochi vecchi",
    "scatola vecchi giochi nintendo",
    "fondo magazzino nintendo",
    "lotto console da testare",
    "giochi nintendo non testati",

    # Inglese (GB/Internazionale)
    "nintendo cartridge bundle",
    "snes cartridge joblot",
    "n64 games bundle joblot",
    "nes cartridge lot",
    "game boy game lot untested",
    "mega drive games bundle joblot",
    "master system cartridge bundle",
    "loft clearance nintendo",
    "attic find video games",
    "garage sale nintendo bundle",
    "untested nintendo lot",

    # Tedesco (DE)
    "nintendo spiele sammlung dachbodenfund",
    "snes spiele konvolut",
    "nintendo 64 spiele sammlung",
    "nes spiele konvolut",
    "game boy spiele sammlung",
    "mega drive spiele konvolut",
    "nintendo kellerfund",
    "nintendo ungetestet sammlung",

    # Francese (FR)
    "lot cartouches nintendo",
    "lot jeux super nintendo snes",
    "lot jeux n64 nintendo 64",
    "lot jeux nes nintendo",
    "lot jeux game boy",
    "lot jeux mega drive sega",
    "vide grenier nintendo",
    "fond de grenier jeux video",
    "jeux nintendo non teste",

    # ==================== NINTENDO 8-BIT (NES / FAMICOM) ====================
    "nes pal gig",
    "mattel nes cartuccia",
    "little samson nes",
    "flintstones dinosaur nes",
    "castlevania nes pal ita",
    "duck tales 2 nes",
    "snow bros nes",
    "panic restaurant nes",
    "bubble bobble 2 nes",
    "mega man nes pal",
    "famicom disk system lot",

    # ==================== SUPER NINTENDO (SNES) ====================
    "snes pal gig",
    "mega man x3 snes",
    "mega man 7 snes",
    "hagane snes",
    "demon crest snes",
    "terranigma pal ita",
    "whirlo snes",
    "castlevania vampire kiss snes",
    "sunset riders snes",
    "wild guns snes",
    "super metroid pal ita",
    "zelda snes pal ita",
    "secret of evermore pal ita",
    "illusion of time pal ita",
    "lufia 2 pal ita",
    "super famicom lot",

    # ==================== NINTENDO 64 (N64) ====================
    "conker bad fur day pal",
    "paper mario n64 pal ita",
    "mario party 3 n64",
    "castlevania legacy darkness n64",
    "snowboard kids 2 n64",
    "stunt racer 64",
    "worms armageddon n64",
    "resident evil 2 n64 pal ita",
    "zelda majora mask n64 pal ita",
    "zelda ocarina time n64 pal ita",

    # ==================== GAME BOY (CLASSIC, COLOR, ADVANCE) ====================
    "trip world game boy",
    "pokemon smeraldo pal ita",
    "pokemon cristallo pal ita",
    "pokemon rosso fuoco pal ita",
    "pokemon foglia verde pal ita",
    "pokemon rubino zaffiro pal ita",
    "ninja cop gba",
    "boktai pal ita",
    "castlevania aria sorrow gba",
    "shantae gbc",
    "metal gear solid gbc",

    # ==================== SEGA A CARTUCCE (MASTER SYSTEM & MEGA DRIVE) ====================
    "alien soldier mega drive",
    "the punisher mega drive",
    "mega man wily wars",
    "castlevania new generation",
    "knuckles chaotix 32x",
    "darxide 32x",
    "smurfs travel world master system",
    "power strike 2 master system",
    "golden axe 3 mega drive",
    "sega nomad console"
]

# Blacklist per eliminare repliche, protezioni e accessori inutili
BLACKLIST = [
    "repro", "riproduzione", "custom", "copia", "falso", "replica", "fake", 
    "reprint", "manuale stampato", "box protector", "custodia protettiva", 
    "salvascatola", "protettore box", "proteggi scatola", "protezione pet", 
    "box plastica", "schutzhülle", "boite de protection", "solo guida", 
    "guida strategica", "poster", "playstation", "ps1", "ps2", "ps3", "ps4", "ps5"
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

def search_ebay_finding(keyword, country_label, global_id, is_first_run=False):
    params = {
        "OPERATION-NAME": "findItemsAdvanced",
        "SERVICE-VERSION": "1.0.0",
        "SECURITY-APPNAME": EBAY_APP_ID.strip(),
        "RESPONSE-DATA-FORMAT": "JSON",
        "REST-PAYLOAD": "",
        "GLOBAL-ID": global_id,
        "keywords": keyword,
        "itemFilter(0).name": "ListingType",
        "itemFilter(0).value": "FixedPrice",
        "sortOrder": "StartTimeNewest",
        "paginationInput.entriesPerPage": "3"
    }
    
    url = f"https://svcs.ebay.com/services/search/FindingService/v1?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
        root = data.get("findItemsAdvancedResponse", [{}])[0]
        ack = root.get("ack", ["Failure"])[0]
        
        if ack != "Success":
            return "API Error", 0

        search_res = root.get("searchResult", [{}])[0]
        items = search_res.get("item", [])
    except Exception:
        return "Err", 0

    inviati = 0
    max_items = 1 if is_first_run else 3

    for item in items[:max_items]:
        item_id = item.get("itemId", [""])[0]
        title = item.get("title", [""])[0]
        item_url = item.get("viewItemURL", [""])[0]
        
        price_info = item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0]
        price_val = price_info.get("__value__", "")
        currency = price_info.get("@currencyId", "")
        price_str = f"{price_val} {currency}"

        if not item_id or not item_url:
            continue

        title_clean = title.lower()
        if item_id in visti:
            continue
        if any(bad_word in title_clean for bad_word in BLACKLIST):
            continue

        visti.add(item_id)

        tag = "📦 <b>Catalogo Esistente</b>" if is_first_run else "🎯 <b>Nuovo Annuncio Cartucce</b>"
        safe_title = html.escape(title)
        safe_kw = html.escape(keyword)

        message = (
            f"{tag} [{country_label}]\n\n"
            f"🕹️ <b>Titolo:</b> {safe_title}\n"
            f"💰 <b>Prezzo:</b> {price_str}\n"
            f"🔍 <b>Filtro:</b> {safe_kw}\n\n"
            f"🔗 <a href='{item_url}'>Apri su eBay {country_label}</a>"
        )

        send_telegram(message)
        inviati += 1
        time.sleep(1.2)

    return "200 (OK)", inviati

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
    send_telegram("🚀 <b>Radar Cartucce & Svuota-Soffitta Attivo!</b>")

    # Scansione iniziale archivio
    for kw in KEYWORDS:
        for country_label, global_id in MARKETPLACES:
            search_ebay_finding(kw, country_label, global_id, is_first_run=True)
            time.sleep(0.4)

    send_telegram("✅ <b>Base cartucce pronta!</b> Ora in ascolto solo per nuovi annunci.")

    # Sentinella in tempo reale
    while True:
        time.sleep(60)
        for kw in KEYWORDS:
            for country_label, global_id in MARKETPLACES:
                search_ebay_finding(kw, country_label, global_id, is_first_run=False)
                time.sleep(0.6)

if __name__ == "__main__":
    main()
