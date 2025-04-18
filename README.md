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
### Scelta tipologia di prodotto
Una volta avviato il programma, si presenta un menu con le seguenti opzioni:
![banner](/imgs/program_start.png)

0. **Exit**: per uscire dal programma.
1. **Cameras**: per mostrare i marchi delle fotocamere.
2. **Lenses**: per mostrare i marchi degli obiettivi.

Ogni ulteriore input è ignorato ed è richiesto di selezionare un'opzione valida.

### Scelta marchio
Una volta selezionata la tipologia di prodotto, viene mostrato un elenco di marchi disponibili. Ad esempio, se si sceglie "Cameras", verrà visualizzato un elenco di marchi di fotocamere.
![brand selection](/imgs/brands_selection.png)

I marchi sono numerati e l'utente può selezionare un marchio inserendo il numero corrispondente. L'utente può anche digitare più marchi separati da uno spazio. 

Ad esempio, se si desidera selezionare i marchi 1 e 3, è possibile digitare `"1 3"` e premere invio. Se si desidera selezionare solo un marchio, è possibile digitare il numero corrispondente e premere invio.

Se non è valido almeno uno dei numeri inseriti, è visualizzato un avviso ed è richiesto di selezionare almeno un marchio valido.

I marchi non validi sono ignorati e il programma procede al tracking dei marchi validi selezionati.

### Tracking
Una volta selezionati i marchi, il programma inizia a monitorare i nuovi prodotti. Durante il monitoraggio, il programma verifica se ci sono nuovi prodotti disponibili per i marchi selezionati.
![tracking](/imgs/select_type_and_brands.png)

### Nuove aggiunte
Nel caso in cui in uno dei marchi selezionati siano stati aggiunti nuovi prodotti, verrà visualizzata una tabella con i dettagli dei nuovi prodotti.

![new products](/imgs/new_additions.png)

Se vengono trovati nuovi prodotti, il programma invia una notifica al bot telegram con i dettagli dei nuovi prodotti.