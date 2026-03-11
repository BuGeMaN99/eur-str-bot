# Telegram Euribor / €STR Bot 🤖

Questo bot recupera giornalmente (alle 08:01) il tasso **€STR (Euro short-term rate)** dal sito web ufficiale della **BCE (Banca Centrale Europea)**, lo incrementa di 8,5 punti base e invia un messaggio formattato in un canale Telegram o chat specifica.

## 🚀 Requisiti

- Python 3.8+
- Token di un bot Telegram (ottenibile tramite [@BotFather](https://t.me/BotFather))
- ID del Canale o Chat Telegram (es. `@strvalue` o ID numerico)

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

3. **Crea e configura il file `.env`**:
   ```bash
   cp .env.example .env
   ```
   Apri il file `.env` inserendo i tuoi dati (il token e l'ID del canale).

4. **Avvia il bot**:
   ```bash
   python3 tassi_bot.py
   ```

---

## 🛠️ Suggerimenti per il Deployment su LXC (Proxmox / Linux)

Per tenere il bot in esecuzione 24/7 nel tuo container LXC (Linux Containers), la soluzione più affidabile è un servizio `systemd`.

Questa guida ti presume loggato nel tuo LXC come root:

1. Assicurati di avere il progetto in una directory stabile, es. `/opt/eur-str-bot/`
   ```bash
   cd /opt/
   # ... (clona il progetto, crea l'ambiente venv, etc.)
   ```

2. Crea un file di servizio col comando:
   ```bash
   nano /etc/systemd/system/eur-str-bot.service
   ```

3. Incolla la seguente configurazione (aggiusta i percorsi `/opt/eur-str-bot` in base a dove hai messo la cartella):
   ```ini
   [Unit]
   Description=Telegram Euribor/ESTR Bot
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/opt/eur-str-bot
   # Usa l'eseguibile Python dal virtual environment che hai creato!
   ExecStart=/opt/eur-str-bot/venv/bin/python /opt/eur-str-bot/tassi_bot.py
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

## 📋 Comandi supportati dal Bot
Puoi inviare questi messaggi al bot in chat privata per testarlo:
- `/start` o `/help`: Messaggio di benvenuto e info base.
- `/status`: Ti conferma che il bot è online ed in esecuzione.
