import os
import csv
import logging
import threading
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template

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

import schedule

app = Flask(__name__)

URL_ECB = 'https://www.ecb.europa.eu/stats/financial_markets_and_interest_rates/euro_short-term_rate/html/index.en.html'
CSV_FILE = 'estr_history.csv'

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

def update_csv_data():
    """Recupera i dati e li salva nel CSV se non sono già presenti per la data odierna."""
    logger.info("Tentativo di aggiornamento giornaliero per il CSV...")
    value_percent, date = fetch_estr_data()
    if value_percent is None:
        logger.error("Fetch fallito, non aggiorno il CSV.")
        return

    try:
        estr_value = float(value_percent.replace('%', '').strip())
        total_value = round(estr_value + 0.085, 3)
        
        # Verifica se il file esiste
        file_exists = os.path.isfile(CSV_FILE)
        
        # Controlla l'ultima data inserita per evitare duplicati
        last_date = None
        if file_exists:
            with open(CSV_FILE, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if len(rows) > 1:
                    last_date = rows[-1][0] # La prima colonna è la data
        
        if last_date != date:
            with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists or os.stat(CSV_FILE).st_size == 0:
                    writer.writerow(['Date', 'ESTR_Value', 'Total_Value'])
                writer.writerow([date, f"{estr_value:.3f}", f"{total_value:.3f}"])
            logger.info(f"Dati salvati in CSV per la data {date}: €STR {estr_value}%, Totale {total_value}%")
        else:
            logger.info(f"Dati per la data {date} già presenti nel CSV. Nessun duplicato inserito.")
            
    except Exception as e:
        logger.error(f"Errore durante l'aggiornamento del CSV: {e}")

def run_schedule():
    """Esegue lo scheduler in loop in un thread separato."""
    schedule.every().day.at("08:00").do(update_csv_data)
    logger.info("Scheduler in background avviato per l'esecuzione giornaliera alle 08:00.")
    while True:
        schedule.run_pending()
        time.sleep(60)

# Avvia lo scraper al bootstrap e poi accende lo scheduler
# L'if serve a prevenire l'esecuzione multipla del task quando Flask ricarica il server in debug
if not os.environ.get("WERKZEUG_RUN_MAIN"):
    update_csv_data()
    scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
    scheduler_thread.start()

def read_csv_data():
    """Legge la storia dal CSV per restituirla al frontend come lista di dicts."""
    history = []
    if os.path.isfile(CSV_FILE):
        with open(CSV_FILE, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                history.append({
                    'date': row['Date'],
                    'estr': float(row['ESTR_Value']),
                    'total': float(row['Total_Value'])
                })
    return history

@app.route('/')
def index():
    logger.info("Richiesta ricevuta per la dashboard delle statistiche.")
    
    # Nel caso remoto in cui il file CSV sia inesistente prima del mount
    if not os.path.isfile(CSV_FILE):
        update_csv_data()
        
    history = read_csv_data()
    
    current_data = history[-1] if history else None
    
    # Calcolo di base delle statistiche
    min_estr = min([d['estr'] for d in history]) if history else 0
    max_estr = max([d['estr'] for d in history]) if history else 0
    avg_estr = (sum([d['estr'] for d in history]) / len(history)) if history else 0
    
    stats = {
        'min': f"{min_estr:.3f}",
        'max': f"{max_estr:.3f}",
        'avg': f"{avg_estr:.3f}"
    }
    
    return render_template(
        'index.html',
        current_data=current_data,
        history=history,
        stats=stats,
        url=URL_ECB
    )

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8345))
    logger.info(f"Avvio del server web sulla porta {PORT}...")
    app.run(host='0.0.0.0', port=PORT)
