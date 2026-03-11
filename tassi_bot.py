import os
import time
import logging
import threading
import requests
from bs4 import BeautifulSoup
import telebot
import schedule
from dotenv import load_dotenv

# Configura il logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Disabilita i warning di urllib3 su macOS
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
try:
    urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)
except AttributeError:
    pass

# Carica le variabili d'ambiente
load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

if not BOT_TOKEN or not CHANNEL_ID:
    logger.error("Token del bot o ID del canale mancanti nel file .env")
    exit(1)

# Crea l'istanza del bot
bot = telebot.TeleBot(BOT_TOKEN)

URL_ECB = 'https://www.ecb.europa.eu/stats/financial_markets_and_interest_rates/euro_short-term_rate/html/index.en.html'

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Benvenuto nel bot notifiche Euribor / €STR!\nUsa /status per verificare che il bot sia attivo.")

@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, "Bot online e in esecuzione. Le notifiche sono programmate ogni giorno alle 08:01.")

def fetch_estr_data():
    """Recupera l'ultimo tasso €STR dal sito della BCE"""
    try:
        response = requests.get(URL_ECB, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table')
        
        if not table:
            logger.error("Impossibile trovare la tabella dei tassi nella pagina HTML.")
            return None, None
            
        values = []
        for row in table.find_all('tr'):
            row_values = [cell.text.strip() for cell in row.find_all('td')]
            if row_values:
                values.append(row_values)
                
        if len(values) >= 2:
            value_str = values[0][0]  # Es: "1.933" o "1.933%"
            date_str = values[1][0]   # Es: "10-03-2026"
            return value_str, date_str
        else:
            logger.error("La tabella non contiene dati sufficienti.")
            return None, None
            
    except Exception as e:
        logger.error(f"Errore durante il recupero dei dati dalla BCE: {e}")
        return None, None

def send_euribor_notification():
    """Recupera i dati e invia la notifica al canale"""
    logger.info("Avvio del recupero dati €STR per la notifica giornaliera...")
    value_percent, date = fetch_estr_data()
    
    if value_percent is None:
        logger.error("Recupero dati fallito, nessuna notifica inviata.")
        return
        
    try:
        estr_value = float(value_percent.replace('%', '').strip())
        total_value = estr_value + 0.085
        
        euribor_link_tag = f'<a href="{URL_ECB}">€STR</a>'
        message = (
            f"Euro short-term rate ({euribor_link_tag}): <b>{estr_value:.3f}%</b>\n"
            f"Somma con 8,5 punti base: <b>{total_value:.3f}%</b>\n"
            f"Ultimo aggiornamento: {date}"
        )
        
        bot.send_message(CHANNEL_ID, message, parse_mode='HTML')
        logger.info(f"Notifica inviata con successo al canale {CHANNEL_ID}")
        
    except ValueError:
        logger.error(f"Errore di conversione sul valore recuperato: {value_percent}")
    except Exception as e:
        logger.error(f"Errore durante l'invio del messaggio su Telegram: {e}")

def main():
    logger.info("Bot in avvio...")
    
    # Schedula il job giornaliero
    schedule.every().day.at("08:01").do(send_euribor_notification)
    logger.info("Job giornaliero configurato per le 08:01")
    
    # Avvia il polling in un thread separato per non bloccare lo scheduler
    def polling_thread():
        while True:
            try:
                bot.polling(none_stop=True, interval=0, timeout=20)
            except Exception as e:
                logger.error(f"Errore nel polling: {e}")
                time.sleep(15)
                
    t = threading.Thread(target=polling_thread)
    t.daemon = True
    t.start()
    logger.info("Bot in ascolto per i comandi (/start, /status, /help)...")
    
    # Loop principale per lo scheduler
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Chiusura del bot in corso...")

if __name__ == '__main__':
    main()
