import os
import logging
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string

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

app = Flask(__name__)

URL_ECB = 'https://www.ecb.europa.eu/stats/financial_markets_and_interest_rates/euro_short-term_rate/html/index.en.html'

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

html_template = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Statistiche Valore €STR</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f7f6;
            color: #333;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background-color: #fff;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 500px;
            width: 100%;
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 20px;
        }
        .stat-box {
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .stat-label {
            font-size: 14px;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        .stat-value {
            font-size: 36px;
            font-weight: bold;
            color: #2980b9;
        }
        .footer {
            margin-top: 20px;
            font-size: 12px;
            color: #95a5a6;
        }
        .error {
            color: #e74c3c;
            font-weight: bold;
        }
        a {
            color: #2980b9;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Statistiche Tassi €STR</h1>
        {% if estr_value %}
            <div class="stat-box">
                <div class="stat-label">Euro short-term rate (<a href="{{ url }}" target="_blank">€STR</a>)</div>
                <div class="stat-value">{{ estr_value }}%</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Somma con 8,5 punti base (+0.085%)</div>
                <div class="stat-value">{{ total_value }}%</div>
            </div>
            <div class="footer">
                Ultimo aggiornamento: {{ date }}
            </div>
        {% else %}
            <div class="error">
                Errore nel recupero dei dati dalla BCE. Riprova più tardi.
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    logger.info("Richiesta ricevuta per la pagina delle statistiche.")
    value_percent, date = fetch_estr_data()
    
    if value_percent is None:
        return render_template_string(html_template, estr_value=None)
        
    try:
        estr_value = float(value_percent.replace('%', '').strip())
        total_value = round(estr_value + 0.085, 3)
        return render_template_string(
            html_template,
            estr_value=f"{estr_value:.3f}",
            total_value=f"{total_value:.3f}",
            date=date,
            url=URL_ECB
        )
    except ValueError:
        logger.error(f"Errore di conversione sul valore recuperato: {value_percent}")
        return render_template_string(html_template, estr_value=None)

if __name__ == '__main__':
    # Espone la web app su una porta casuale, es. 8345
    PORT = int(os.environ.get('PORT', 8345))
    logger.info(f"Avvio del server web sulla porta {PORT}...")
    app.run(host='0.0.0.0', port=PORT)
