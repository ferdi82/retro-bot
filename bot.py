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
    # Occasioni & Lotti
    "svuoto soffitta giochi",
    "vecchi giochi nintendo",
    "cassette nintendo",
    "giochi anni 90",
    "blocco videogiochi vecchi",
    "lotto videogiochi infanzia",
    "scatola vecchi giochi",

    # Distribuzione & Collezionismo
    "pal gig",
    "distribuzione gig",
    "mattel nes",
    "black label ps1",
    "snes cib",
    "n64 cib",
    "game boy cib",
    "sigillato nintendo",

    # Console 5ª Gen (32/64 bit)
    "sega saturn console",
    "playstation 1 scatola",
    "ps1 console box",
    "nintendo 64 console",
    "3do interactive",
    "atari jaguar console",
    "amiga cd32",

    # Console 4ª Gen (16 bit)
    "super nintendo console",
    "snes console scatola",
    "sega mega drive console",
    "sega mega cd",
    "pc engine console",
    "neo geo aes console",

    # Console 3ª Gen & Retro
    "nintendo nes console",
    "famicom disk system",
    "sega master system console",
    "atari 2600 console",
    "vectrex console",

    # Portatili
    "game boy classic scatola",
    "game boy color box",
    "game boy advance box",
    "game boy micro",
    "virtual boy console",
    "game & watch nintendo",

    # Giochi Rari
    "panzer dragoon saga",
    "snatcher sega",
    "suikoden 2 pal ita",
    "castlevania symphony of the night pal",
    "tombi ps1",
    "klonoa ps1",
    "kula world ps1",
    "silent hill ps1 pal ita",
    "conker bad fur day pal",
    "paper mario n64 pal ita",
    "mega man x3 snes",
    "hagane snes",
    "terranigma pal ita",
    "whirlo snes",
    "super metroid big box",
    "little samson nes",
    "snow bros nes",
    "pokemon smeraldo box",

    # Scatole, Manuali & Lotti
    "snes solo scatola",
    "scatola super nintendo",
    "n64 box only",
    "ps1 scatola vuota",
    "manuale istruzioni snes",
    "lotto retrogaming pal ita",
    "fondo magazzino videogiochi"
]

BLACKLIST = [
    "repro", "riproduzione", "custom", "copia", "falso", "replica", "fake", 
    "custodia vuota ps4", "custodia vuota ps5", "cover art only", "manuale stampato",
    "reprint", "manuale pdf", "box protector", "custodia protettiva", "salvascatola", 
    "protettore box", "proteggi scatola", "protezione pet", "box plastica", 
    "schutzhülle", "boite de protection", "solo guida", "guida strategica", "poster"
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

def fetch_feed(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            content = resp.read()
            return resp.getcode(), feedparser.parse(content)
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return str(e), None

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
    send_telegram("🚀 <b>Test di Connessione a eBay...</b>")

    # Test di diagnostica sulla prima parola chiave
    test_status, test_found = check_ebay("game boy console", "IT", "https://www.ebay.it", is_first_run=True)
    send_telegram(f"🔍 <b>Diagnostica eBay:</b>\n- Risposta server: <code>{test_status}</code>\n- Annunci rilevati: <code>{test_found}</code>")

    # 1. Scansione archivio esistente
    for kw in KEYWORDS:
        for domain_name, base_url in EBAY_DOMAINS:
            check_ebay(kw, domain_name, base_url, is_first_run=True)
            time.sleep(0.5)

    send_telegram("✅ <b>Base pronta!</b> Da ora in avanti riceverai solo i nuovi annunci pubblicati.")

    # 2. Monitoraggio continuo per soli nuovi arrivi
    while True:
        time.sleep(60)
        for kw in KEYWORDS:
            for domain_name, base_url in EBAY_DOMAINS:
                check_ebay(kw, domain_name, base_url, is_first_run=False)
                time.sleep(0.8)

if __name__ == "__main__":
    main()
