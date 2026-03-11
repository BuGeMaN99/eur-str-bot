# Web App Statistiche Euribor / €STR 📊

Questa applicazione web recupera in tempo reale il tasso **€STR (Euro short-term rate)** dal sito web ufficiale della **BCE (Banca Centrale Europea)**, lo incrementa di 8,5 punti base e mostra i risultati su una pagina web dedicata ed esposta tramite porta.

## 🚀 Requisiti

- Python 3.8+

## ⚙️ Installazione e Configurazione Rapida (Sviluppo)

1. **Clona la repository**:
   ```bash
   git clone https://github.com/andreabugetti/eur-str-bot.git
   cd eur-str-bot
   ```

2. **Crea un virtual environment e installa le dipendenze**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Avvia il server**:
   ```bash
   python3 app.py
   ```
   L'applicazione di default sarà esposta sulla porta `8345`. Puoi specificare una porta diversa passando la variabile d'ambiente `PORT`:
   ```bash
   PORT=8080 python3 app.py
   ```

## 🛠️ Suggerimenti per il Deployment su LXC (Proxmox / Linux)

Per tenere l'applicazione in esecuzione 24/7 nel tuo container LXC (Linux Containers), la soluzione più affidabile è un servizio `systemd`.

Questa guida ti presume loggato nel tuo LXC come root:

1. Assicurati di avere il progetto in una directory stabile, es. `/opt/bots/eur-str-bot/`
   ```bash
   cd /opt/bots/
   # ... (clona il progetto, crea l'ambiente venv, etc.)
   ```

2. Crea un file di servizio col comando:
   ```bash
   nano /etc/systemd/system/eur-str-bot.service
   ```

3. Incolla la seguente configurazione (aggiusta i percorsi `/opt/bots/eur-str-bot` in base a dove hai messo la cartella):
   ```ini
   [Unit]
   Description=EUR/ESTR Web App
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/opt/bots/eur-str-bot
   # Puoi configurare la porta della UI specificando la variabile d'ambiente PORT (es: 80)
   Environment="PORT=8345"
   # Usa l'eseguibile Python dal virtual environment che hai creato!
   ExecStart=/opt/bots/eur-str-bot/venv/bin/python /opt/bots/eur-str-bot/app.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

4. Abilita il servizio all'avvio e falllo partire:
   ```bash
   systemctl daemon-reload
   systemctl enable eur-str-bot.service
   systemctl start eur-str-bot.service
   ```

5. **Controlla i log** in tempo reale per verificare che tutto funzioni:
   ```bash
   journalctl -u eur-str-bot.service -f
   ```
