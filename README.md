```
███╗   ██╗ ██████╗  ██████╗    ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗ 
████╗  ██║██╔═══██╗██╔════╝    ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
██╔██╗ ██║██║   ██║██║         ███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝
██║╚██╗██║██║   ██║██║         ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗
██║ ╚████║╚██████╔╝╚██████╗    ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║
╚═╝  ╚═══╝ ╚═════╝  ╚═════╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
                                                           by Alessandro Monetti - 2025
```

# ITA
***Benvenuti!***

Questo software nasce dalla necessità di cercare una buona offerta per un obiettivo per conto di un amico su [NewOldCamera](https://www.newoldcamera.com/). 

Avendo già perso almeno un'occasione per segnalargli un affare, ho deciso con la scusa di mettermi alla prova e scrivere un web scraper con un semplice sistema di notifiche via bot telegram.

## Strumenti
- **Python**
- **BeautifulSoup**: scraping lista dei marchi
- **Requests**: richieste HTTP
- **Pandas**: gestione dei dati
- **Telegram**: invio notifiche

## Configurazione
### Virtual Environment
L'ambiente virtuale è stato creato con [poetry](https://python-poetry.org/), un gestore di pacchetti per Python. Per installarlo, puoi seguire le istruzioni ufficiali [qui](https://python-poetry.org/docs/#installation).

Per installare le dipendenze, esegui il seguente comando (assicurati di essere nella cartella del progetto):
```bash
poetry install
```


## Esecuzione
Per attivare l'ambiente virtuale, esegui:
```bash
poetry env activate
```

Per eseguire il programma, utilizza il comando:
```bash
poetry run python noc_scraper.py
```

### Bot telegram
Per utilizzare il bot telegram è necessario creare un bot e ottenere un token. Per farlo, segui questi passaggi:

1. Apri Telegram e cerca il bot "BotFather".
2. Invia il comando `/newbot` e segui le istruzioni per creare un nuovo bot.
3. Una volta creato il bot, riceverai un token di accesso. Copia questo token e incollalo nel file `telegram_data.json` nel seguente formato
```json
{
    "chat_id": "YOUR_CHAT_ID",
    "api_key": "YOUR_API_KEY"
}
```
4. Il `chat_id` può essere anche l'handle del tuo profilo telegram, ad esempio `@my_handle`. Il bot invierà un messaggio privato al tuo profilo.


## Il software (WORK IN PROGRESS)
![banner](/imgs/program_start.png)