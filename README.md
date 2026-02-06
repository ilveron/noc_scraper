# NOC Scraper

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**NOC Scraper** e' uno strumento CLI per il monitoraggio automatizzato della sezione "Usato" del sito *New Old Camera*. Il software rileva nuovi prodotti (Fotocamere o Obiettivi) per i marchi specificati e invia notifiche tramite Telegram.

---

## Documentazione in Italiano

### Funzionalita'
* **Monitoraggio costante:** Controllo automatico del sito a intervalli regolari (default: 60 secondi).
* **Modalita' Ibrida:** Utilizzabile sia tramite menu interattivo che via argomenti da riga di comando (CLI).
* **Filtri:** Monitoraggio selettivo per brand (es. solo "Leica" o "Nikon").
* **Notifiche Telegram:** Alert contenenti modello, stato e prezzo.
* **Resilienza:** Gestione automatica degli errori di connessione.

### Installazione

Il progetto utilizza **Poetry** per la gestione delle dipendenze. Assicurati di averlo installato sul tuo sistema.

1.  **Clona il repository:**
    ```bash
    git clone https://github.com/ilveron/noc_scraper.git
    cd noc-scraper
    ```

2.  **Installa le dipendenze:**
    ```bash
    poetry install
    ```

### Configurazione

Per abilitare le notifiche e' necessario configurare un bot Telegram.

1.  Rinomina il file `.env.example` in `.env` (se presente) o creane uno nuovo nella root del progetto.
2.  Inserisci le credenziali ottenute da BotFather:

```ini
TELEGRAM_API_KEY=tuo_token_qui
TELEGRAM_CHAT_ID=tuo_chat_id_qui
```

### Utilizzo

E' possibile avviare lo script in due modalita' tramite `poetry`.

#### 1. Modalita' Interattiva
Avvia lo script senza argomenti per visualizzare il menu di selezione.
```bash
poetry run python main.py
```

#### 2. Modalita' CLI (Automazione)
Passa gli argomenti direttamente da riga di comando per saltare i menu. Utile per cronjob o esecuzioni rapide.

* **Sintassi:**
    ```bash
    poetry run python main.py --type [camera|lens] --brands "Brand1, Brand2"
    ```

* **Esempi:**
    ```bash
    # Monitora fotocamere Sony e Nikon Z
    poetry run python main.py --type camera --brands "Sony, Nikon Z"

    # Monitora obiettivi Canon EOS R
    poetry run python main.py --type lens --brands "Canon EOS R"
    ```

---

## English Documentation

### Features
* **Continuous Monitoring:** Automatically checks the website at regular intervals (default: 60s).
* **Hybrid Mode:** Works via interactive menus or Command Line Arguments (CLI).
* **Filters:** Monitor specific brands only.
* **Telegram Alerts:** Notifications include model, condition, and price.
* **Error Handling:** Automatically manages connection timeouts and retries.

### Installation

This project uses **Poetry** for dependency management.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ilveron/noc_scraper.git
    cd noc-scraper
    ```

2.  **Install dependencies:**
    ```bash
    poetry install
    ```

### Configuration

To receive notifications, configure your Telegram Bot credentials.

1.  Create a `.env` file in the project root.
2.  Add your API Key and Chat ID:

```ini
TELEGRAM_API_KEY=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### Usage

Run the script using `poetry`.

#### 1. Interactive Mode
Run without arguments to launch the selection menu.
```bash
poetry run python main.py
```

#### 2. CLI Mode (Automation)
Pass arguments to skip the interactive prompts.

* **Syntax:**
    ```bash
    poetry run python main.py --type [camera|lens] --brands "Brand1, Brand2"
    ```

* **Examples:**
    ```bash
    # Track Sony and Nikon cameras
    poetry run python main.py --type camera --brands "Sony, Nikon"

    # Track Leica lenses
    poetry run python main.py --type lens --brands "Leica"
    ```

---

### Disclaimer

**IT:** Questo software è stato creato a scopo didattico. L'autore non è affiliato con NewOldCamera. Utilizzare con responsabilità per non sovraccaricare il server.

**EN:** This software is for educational purposes only. The author is not affiliated with NewOldCamera. Please use responsibly to avoid server overload.
