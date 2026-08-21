import base64
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

# Credenziali Ufficiali eBay Production
EBAY_CLIENT_ID = "Ferdinan-Myretrob-PRD-60149ee33-875cf987"
EBAY_CLIENT_SECRET = "PRD-0149ee33b990-e288-4d81-83c2-df6e"

MARKETPLACES = [
    ("IT", "EBAY-IT"),
    ("DE", "EBAY-DE"),
    ("FR", "EBAY-FR"),
    ("GB", "EBAY-GB"),
]

KEYWORDS = [
    # Occasioni & Lotti
    "svuoto soffitta giochi",
    "svuoto cantina nintendo",
    "vecchi giochi nintendo",
    "cassette nintendo",
    "cassette super nintendo",
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
    "casio loopy",
    "bandai playdia",

    # Console 16 Bit & Retro
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
    "nintendo nes console",
    "atari 2600 console",
    "vectrex console",

    # Portatili
    "game boy classic scatola",
    "game boy color box",
    "game boy advance box",
    "game boy micro",
    "virtual boy console",
    "sega game gear console",
    "sega nomad",
    "atari lynx console",
    "game & watch nintendo",

    # Giochi Rari
    "panzer dragoon saga",
    "shining force 3 saturn",
    "deep fear saturn",
    "snatcher sega",
    "suikoden 2 pal ita",
    "castlevania symphony of the night pal",
    "tombi ps1 pal ita",
    "tombi 2 ps1",
    "klonoa ps1",
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
    "little samson nes",
    "snow bros nes",
    "pokemon smeraldo box",
    "pokemon cristallo box",

    # Scatole e manuali
    "snes solo scatola",
    "scatola super nintendo",
    "n64 box only",
    "game boy box only",
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
current_token = None
token_expires_at = 0
last_auth_error = "Nessun errore"

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

def get_ebay_oauth_token():
    global current_token, token_expires_at, last_auth_error
    if current_token and time.time() < token_expires_at:
        return current_token

    # Pulizia credenziali da eventuali spazi o caratteri invisibili
    client_id = EBAY_CLIENT_ID.strip()
    client_secret = EBAY_CLIENT_SECRET.strip()

    # Formattazione corretta RFC per Basic Auth
    auth_bytes = f"{client_id}:{client_secret}".encode("utf-8")
    b64_auth = base64.b64encode(auth_bytes).decode("utf-8")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {b64_auth}"
    }
    
    # Body con scope esplicito corretto per le API Browse
    params = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request("https://api.ebay.com/identity/v1/oauth2/token", data=data, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            current_token = res_json.get("access_token")
            token_expires_at = time.time() + res_json.get("expires_in", 7200) - 120
            return current_token
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        last_auth_error = f"HTTP {e.code}: {err_msg}"
        return None
    except Exception as e:
        last_auth_error = str(e)
        return None

def search_ebay_api(keyword, country_label, global_id, is_first_run=False):
    token = get_ebay_oauth_token()
    if not token:
        return f"Auth Error ({last_auth_error})", 0

    query = urllib.parse.quote_plus(keyword)
    api_url = f"https://api.ebay.com/buy/browse/v1/item_summary/search?q={query}&filter=buyingOptions:{{FIXED_PRICE}}&sort=newlyListed&limit=3"

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": global_id,
        "Accept": "application/json"
    }

    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("itemSummaries", [])
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}", 0
    except Exception as e:
        return f"Err: {str(e)[:15]}", 0

    inviati = 0
    max_items = 1 if is_first_run else 3

    for item in items[:max_items]:
        item_id = item.get("itemId")
        title = item.get("title", "")
        item_url = item.get("itemWebUrl", "")
        price_dict = item.get("price", {})
        price_str = f"{price_dict.get('value', '')} {price_dict.get('currency', '')}"

        if not item_id or not item_url:
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
            f"{tag} [{country_label}]\n\n"
            f"📦 <b>Titolo:</b> {safe_title}\n"
            f"💰 <b>Prezzo:</b> {price_str}\n"
            f"🔍 <b>Filtro:</b> {safe_kw}\n\n"
            f"🔗 <a href='{item_url}'>Apri su eBay {country_label}</a>"
        )

        send_telegram(message)
        inviati += 1
        time.sleep(1.2)

    return "200 (API OK)", inviati

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
    send_telegram("🚀 <b>Test eBay API Ufficiale...</b>")

    test_status, test_found = search_ebay_api("game boy", "IT", "EBAY-IT", is_first_run=True)
    send_telegram(f"🔍 <b>Diagnostica API:</b>\n- Risposta: <code>{test_status}</code>\n- Annunci caricati: <code>{test_found}</code>")

    # Scansione iniziale archivio
    for kw in KEYWORDS:
        for country_label, global_id in MARKETPLACES:
            search_ebay_api(kw, country_label, global_id, is_first_run=True)
            time.sleep(0.4)

    send_telegram("✅ <b>Base pronta!</b> Da ora in avanti riceverai solo i nuovi annunci pubblicati.")

    # Sentinella in tempo reale
    while True:
        time.sleep(60)
        for kw in KEYWORDS:
            for country_label, global_id in MARKETPLACES:
                search_ebay_api(kw, country_label, global_id, is_first_run=False)
                time.sleep(0.6)

if __name__ == "__main__":
    main()
