import html
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

# ==================== CONFIGURAZIONE ====================
TELEGRAM_TOKEN = "8953657931:AAHiJknl8lm08CaU82NyZZN_HAeFw3iAaU4"
CHAT_ID = "5463779"
EBAY_APP_ID = "Ferdinan-Myretrob-PRD-60149ee33-875cf987"

# Percentuale minima di margine per considerare un'inserzione un affare (19% o superiore)
MIN_PROFIT_MARGIN = 19.0

MARKETPLACES = [
    ("IT", "EBAY-IT"),
    ("DE", "EBAY-DE"),
    ("FR", "EBAY-FR"),
    ("GB", "EBAY-GB"),
]

KEYWORDS = [
    # Occasioni & Svuota-Soffitta
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
    "nintendo cartridge bundle",
    "snes cartridge joblot",
    "n64 games bundle joblot",
    "nes cartridge lot",
    "game boy game lot untested",
    "mega drive games bundle joblot",
    "master system cartridge bundle",
    "loft clearance nintendo",
    "attic find video games",
    "snes spiele konvolut",
    "nintendo 64 spiele sammlung",
    "nes spiele konvolut",
    "game boy spiele sammlung",
    "lot cartouches nintendo",
    "lot jeux super nintendo snes",
    "lot jeux n64 nintendo 64",
    "lot jeux nes nintendo",
    "vide grenier nintendo",

    # Giochi di Riferimento & Rari (Cartucce)
    "adventure island nes",
    "adventure island snes",
    "little samson nes",
    "flintstones dinosaur nes",
    "castlevania nes pal ita",
    "duck tales 2 nes",
    "snow bros nes",
    "panic restaurant nes",
    "bubble bobble 2 nes",
    "mega man nes pal",
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
    "conker bad fur day pal",
    "paper mario n64 pal ita",
    "mario party 3 n64",
    "castlevania legacy darkness n64",
    "snowboard kids 2 n64",
    "trip world game boy",
    "pokemon smeraldo pal ita",
    "pokemon cristallo pal ita",
    "pokemon rosso fuoco pal ita",
    "pokemon foglia verde pal ita",
    "alien soldier mega drive",
    "the punisher mega drive",
    "mega man wily wars"
]

BLACKLIST = [
    "repro", "riproduzione", "custom", "copia", "falso", "replica", "fake", 
    "reprint", "manuale stampato", "box protector", "custodia protettiva", 
    "salvascatola", "protettore box", "proteggi scatola", "protezione pet", 
    "box plastica", "schutzhülle", "boite de protection", "solo guida", 
    "guida strategica", "poster", "playstation", "ps1", "ps2", "ps3", "ps4", "ps5"
]

visti = set()
market_value_cache = {}

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

def get_market_average(clean_title, global_id):
    """Calcola la media del valore di mercato interrogando gli annunci venduti e completati."""
    if clean_title in market_value_cache:
        return market_value_cache[clean_title]

    # Estrae parole chiave significative per identificare il gioco
    words = [w for w in re.sub(r"[^a-zA-Z0-9 ]", " ", clean_title).split() if len(w) > 2][:4]
    search_q = " ".join(words)
    if not search_q:
        return None

    params = {
        "OPERATION-NAME": "findCompletedItems",
        "SERVICE-VERSION": "1.0.0",
        "SECURITY-APPNAME": EBAY_APP_ID.strip(),
        "RESPONSE-DATA-FORMAT": "JSON",
        "REST-PAYLOAD": "",
        "GLOBAL-ID": global_id,
        "keywords": search_q,
        "itemFilter(0).name": "SoldItemsOnly",
        "itemFilter(0).value": "true",
        "sortOrder": "EndTimeSoonest",
        "paginationInput.entriesPerPage": "8"
    }

    url = f"https://svcs.ebay.com/services/search/FindingService/v1?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        root = data.get("findCompletedItemsResponse", [{}])[0]
        items = root.get("searchResult", [{}])[0].get("item", [])
        
        prices = []
        for it in items:
            try:
                val = float(it.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", 0))
                if val > 0:
                    prices.append(val)
            except Exception:
                continue

        if len(prices) >= 2:
            avg_price = sum(prices) / len(prices)
            market_value_cache[clean_title] = avg_price
            return avg_price
    except Exception:
        pass

    return None

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
        if root.get("ack", ["Failure"])[0] != "Success":
            return "API Error", 0

        items = root.get("searchResult", [{}])[0].get("item", [])
    except Exception:
        return "Err", 0

    inviati = 0
    max_items = 1 if is_first_run else 3

    for item in items[:max_items]:
        item_id = item.get("itemId", [""])[0]
        title = item.get("title", [""])[0]
        item_url = item.get("viewItemURL", [""])[0]
        
        price_info = item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0]
        price_val_str = price_info.get("__value__", "0")
        currency = price_info.get("@currencyId", "EUR")
        
        try:
            current_price = float(price_val_str)
        except ValueError:
            current_price = 0.0

        if not item_id or not item_url:
            continue

        title_clean = title.lower()
        if item_id in visti:
            continue
        if any(bad_word in title_clean for bad_word in BLACKLIST):
            continue

        visti.add(item_id)

        # Analisi margine di profitto rispetto al mercato
        market_val = get_market_average(title_clean, global_id)
        is_deal = False
        margin_pct = 0.0
        profit_est = 0.0

        if market_val and market_val > current_price and current_price > 0:
            margin_pct = ((market_val - current_price) / market_val) * 100
            profit_est = market_val - current_price
            if margin_pct >= MIN_PROFIT_MARGIN:
                is_deal = True

        safe_title = html.escape(title)
        safe_kw = html.escape(keyword)

        if is_deal:
            message = (
                f"🚨 <b>AFFARE RILEVATO (+{margin_pct:.1f}% di margine)</b> [{country_label}]\n\n"
                f"🕹️ <b>Titolo:</b> {safe_title}\n"
                f"💰 <b>Prezzo Offerta:</b> {current_price:.2f} {currency}\n"
                f"📊 <b>Valore Medio Mercato:</b> ~{market_val:.2f} {currency}\n"
                f"📈 <b>Margine Stimato:</b> +{profit_est:.2f} {currency} (-{margin_pct:.0f}%)\n"
                f"🔍 <b>Filtro:</b> {safe_kw}\n\n"
                f"🔗 <a href='{item_url}'>ACQUISTA SUBITO SU EBAY</a>"
            )
        else:
            tag = "📦 <b>Catalogo Esistente</b>" if is_first_run else "🎯 <b>Nuovo Annuncio</b>"
            message = (
                f"{tag} [{country_label}]\n\n"
                f"🕹️ <b>Titolo:</b> {safe_title}\n"
                f"💰 <b>Prezzo:</b> {current_price:.2f} {currency}\n"
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
    send_telegram(f"🚀 <b>Radar Arbitraggio & Cartucce Attivo!</b>\nFiltro margine minimo impostato a: <b>{MIN_PROFIT_MARGIN}%</b>")

    # Scansione catalogo iniziale
    for kw in KEYWORDS:
        for country_label, global_id in MARKETPLACES:
            search_ebay_finding(kw, country_label, global_id, is_first_run=True)
            time.sleep(0.4)

    send_telegram("✅ <b>Monitoraggio live attivo!</b> Riceverai notifiche standard e alert dedicati con margine $\ge$ 19%.")

    # Scansione continua in tempo reale
    while True:
        time.sleep(60)
        for kw in KEYWORDS:
            for country_label, global_id in MARKETPLACES:
                search_ebay_finding(kw, country_label, global_id, is_first_run=False)
                time.sleep(0.6)

if __name__ == "__main__":
    main()
