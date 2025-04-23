import requests as http
import json

from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from pandas import *
from urllib.parse import quote_plus
import time

from datetime import timedelta
from rich.live import Live
from rich.panel import Panel

set_option("future.no_silent_downcasting", True)

BANNER = \
f'''
███╗   ██╗ ██████╗  ██████╗    ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗ 
████╗  ██║██╔═══██╗██╔════╝    ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
██╔██╗ ██║██║   ██║██║         ███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝
██║╚██╗██║██║   ██║██║         ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗
██║ ╚████║╚██████╔╝╚██████╗    ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║
╚═╝  ╚═══╝ ╚═════╝  ╚═════╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
                                                           by Alessandro Monetti - 2025
'''
USED_CAMERAS_BRANDS_URL = "https://www.newoldcamera.com/_Marche.aspx?Tipo=CO&Bottega=Usato"
USED_LENSES_BRANDS_URL = "https://www.newoldcamera.com/_Marche.aspx?Tipo=OB&Bottega=Usato"
API_URL = "https://apinocservice.azurewebsites.net/api/products"

console = Console()
WARNING_COLOR = "bold yellow"
INFO_COLOR = "bold green"
NEW_COLOR = "bold blue"

SLEEP_TIME = 60

ITEM_TYPES = ["camera", "lens"]

'''
The following function fetches the list of brands from the specified URL.
It uses the requests library to send a GET request to the URL.
The response is parsed using BeautifulSoup to extract the brand names.
The function returns a list of brand names.
'''
def fetch_brands_list(item_type: str = "lens") -> list[str]:
    brands = []
    try:
        if item_type == "camera":
            result = http.get(USED_CAMERAS_BRANDS_URL)
        elif item_type == "lens":
            result = http.get(USED_LENSES_BRANDS_URL)
    except Exception as e:
        console.log(f"Error fetching brands list: {e}", style="bright red")
        return brands
    
    soup = BeautifulSoup(result.text, "html.parser")
    elements = soup.find_all("a", {"class": "txtelenco"})
    
    for elem in elements:
        brands.append(elem.text)

    return brands

'''
The following function takes the split user input and the total number of brands.
It checks if the input is a valid number and within the range of available brands.
If the input is valid, it appends the number to a list.
If the input is 0 (exit) and it's the only input, it appends 0 to the list and returns.
If the input is invalid, it ignores it and continues to the next one.

desired_brand_numbers: A list of strings representing the user input.
total_brands_number: The total number of brands available.
The function returns a list of sanitized brand numbers.
'''
def sanitize_brand_numbers(desired_brand_numbers: list[str], total_brands_number: int) -> list[int]:
    sanitized_brand_numbers = []

    for num in desired_brand_numbers:
        try:
            int_num = int(num)

            # Special check for the exit value (0)
            if int_num == 0:
                if len(desired_brand_numbers) == 1:
                    sanitized_brand_numbers.append(int_num)
                    break
                else:
                    console.log(f"WARNING: Exit value (0) is ignored if passed with other values", style=WARNING_COLOR)
                    continue
            
            if int_num > 0 and int_num <= total_brands_number:
                if int_num not in sanitized_brand_numbers:
                    # Avoid duplicates
                    sanitized_brand_numbers.append(int_num)
                else:
                    console.log(f"WARNING: Value {num} is a duplicate, ignoring", style=WARNING_COLOR)
            else:
                console.log(f"WARNING: Value {num} is not a number in the range (1 - {total_brands_number}), ignoring", style=WARNING_COLOR)
        except ValueError as e:
            console.log(f"WARNING: Value {num} is not a valid integer number, ignoring", style=WARNING_COLOR)
    
    return sanitized_brand_numbers


'''
The following function takes a list of brand numbers and a list of brand names.
It retrieves the brand names corresponding to the specified numbers.

brand_numbers: A list of integers representing the brand numbers given by the user.
brands: A list of strings representing the brand names.
The function returns a list of brand names corresponding to the specified numbers.
'''
def get_brand_names_from_numbers(brand_numbers: list[int], brands: list[str]) -> list[str]:
    desired_brands = []

    for idx in range(len(brands)):
        if idx+1 in brand_numbers:
            desired_brands.append(brands[idx])
    
    return desired_brands


'''
The following function builds the payloads for the API requests.
It takes the brand, item type, and item status as input.
It constructs the payload string by concatenating the parameters with '&' and '='.
The payload string is then returned.

brand: The brand of the item (e.g., "SONY", "CANON").
item_type: The type of item (e.g., "CO" for camera, "OB" for lens).
item_status: The status of the item (e.g. "Usato" for used items, "Nuovo" for new ones).
The function returns a dictionary of payloads for each brand.
'''
def build_payloads(brand_names: list[str], item_type: str, item_status: str) -> dict[str, str]:
    # EXAMPLE NEW CAMERA PAYLOAD:       marca=FUJIFILM+X&tipo=CO&disponibile=M&bottega=Nuovo&path=Upload
    # EXAMPLE USED LENS PAYLOAD:        marca=ASAHI+PENTAX&tipo=OB&disponibile=M&bottega=Usato&path=Upload
    # EXAMPLE USED CAMERA PAYLOAD:      marca=SONY&tipo=CO&disponibile=M&bottega=Usato&path=Upload
    brands_payloads = {}

    for brand in brand_names:
        url_encoded_brand = quote_plus(brand)
        payload = f"marca={url_encoded_brand}&tipo={item_type}&disponibile=M&bottega={item_status}&path=Upload"
        brands_payloads[brand] = payload
    
    return brands_payloads


'''
The following function takes a payload string as input.
It sends a POST request to the API URL with the payload as data.
The response is parsed as JSON, and the "Result" field is extracted.

payload: The payload string to be sent in the POST request.
The function returns the JSON data as a list of dictionaries.
'''
def get_json_data_from_request(payload: str) -> list[dict]:
    try:
        result = http.post(API_URL, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
        json_data = json.loads(result.text)["Result"]
    except Exception as e:
        console.log(f"Error fetching JSON data: {e}", style="bright red")
        return []
    return json_data
    


'''
The following function takes a dictionary of brand names and their corresponding payloads.
It iterates through the dictionary and sends a POST request for each brand.
It retrieves the JSON data for each brand and stores it in a new dictionary.

brands_payloads: A dictionary where the keys are brand names and the values are payload strings.
The function returns a dictionary where the keys are brand names and the values are lists of dictionaries containing the JSON data.
'''
def get_brands_data(brands_payloads: dict[str, str]) -> dict[str, list[dict]]:
    brands_data = {}

    # Do request and get data in json format, per brand name
    for brand, payload in brands_payloads.items():
        data = get_json_data_from_request(payload)
        brands_data[brand] = data
    
    return brands_data

'''
The following function takes a dictionary of brand names and their corresponding data.
It converts each brand's data into a DataFrame and adds a new column for the brand name.

brands_data: A dictionary where the keys are brand names and the values are lists of dictionaries containing the JSON data.
The function returns a dict of DataFrames, each representing the data for a specific brand.
'''
def convert_to_dataframe(brands_data: dict[str, list[dict]]) -> dict[str, DataFrame]:
    brands_dataframes = {}

    # Convert each brand data to a DataFrame
    for brand, data in brands_data.items():
        df = DataFrame(data)
         # Keep only useful columns
        df = df[["ID", "marca", "modello", "novita", "prezzopromozione", "prenotato", "prezzovendita", "stato"]]

        # Replace 0 and 1 in "prenotato" with "False" and "True"
        df["prenotato"] = df["prenotato"].replace({0: False, 1: True})

        brands_dataframes[brand] = df

    return brands_dataframes

'''
The following function takes a brand name and a DataFrame as input.
It creates a table using the rich library to display the new products for that brand.

brand: The brand name for which the table is created.
df: The DataFrame containing the new products for the brand.
The function returns a Table object containing the new products.'''
def get_table_from_additions(item_type: str, brand: str, df: DataFrame) -> Table:
    table = Table(title = f"New products for {brand}")

    table.add_column("Brand", justify="left", style="red")
    table.add_column("Model", justify="left", style="cyan")
    table.add_column("Price", justify="right", style="green")
    table.add_column("status", justify="center", style="white")
    table.add_column("Reserved", justify="center", style="yellow")
    
    for _, row in df.iterrows():
        table.add_row(
            row["marca"],
            row["modello"],
            str(row["prezzovendita"])+"€",
            row["stato"],
            str(row["prenotato"]),
        )

    return table

'''
The following function generates a message to be sent to Telegram.
It takes the brand name, item type, and a DataFrame of new products as input.
It constructs a message string that includes the brand name, item type, and a list of new products with their details.

brand: The brand name for which the message is generated.
item_type: The type of item (e.g., "camera", "lens").
new_products: A DataFrame containing the new products for the brand.
The function returns a string containing the formatted message.
'''
def generate_message(brand: str, item_type: str, new_products: DataFrame) -> str:
    if item_type == "camera":
        item_type += "s"
    elif item_type == "lens":
        item_type += "es"
    
    message = f"New <b>{item_type}</b> added for <b><i>{brand}</i></b>\nHere's a list:"

    for _, row in new_products.iterrows():
        model = row["modello"]
        price = row["prezzovendita"]
        state = row["stato"]
        message += f"\n    <b>{model}</b> (<i>{state}</i>) - {price}€"
    
    return message


def get_telegram_credentials(filename: str) -> dict[str, str]:
    data = None
    with open(filename, "r") as f:
        data = json.loads(f.read())
    return data
    
'''
The following function sends a message to a Telegram chat using the Telegram Bot API.
It constructs the URL for sending the message and sends a POST request with the message payload.

message: The message to be sent.
chat_id: The chat ID of the recipient.
api_key: The API key of the Telegram bot.
parse_mode: The parse mode for the message (default is "HTML").
The function returns the response from the Telegram API as a dictionary.
'''
def send_telegram_message(message: str, chat_id: str, api_key: str, parse_mode = "HTML") -> dict:
    url = f"https://api.telegram.org/bot{api_key}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode,
    }
    try:
        response = http.post(url, json=payload)
        return response.json()
    except Exception as e:
        console.log(f"Error sending telegram message: {e}", style="bright red")
        return {}


def print_item_types():
    console.print(f"[bold red]1.[/bold red]\tCameras", highlight=False)
    console.print(f"[bold red]2.[/bold red]\tLenses", highlight=False)


def print_brands_list(brands: str):
    for idx in range(len(brands)):
        console.print(f"[bold red]{idx+1}.[/bold red]\t{brands[idx]}", highlight=False)


def exit_program():
    console.print()
    console.log("Exiting, bye!", style=INFO_COLOR)
    exit(0)


'''
The following function prompts the user to select the type of items they want to keep track of.
It displays a list of item types and waits for the user to input their choice.
The function returns the selected item type number.
The function also handles invalid input and provides a warning message if the input is not valid.

The function returns an integer representing the selected item type number.
'''
def get_desired_item_type():
    desired_item_type_num = -1

    while desired_item_type_num not in range(len(ITEM_TYPES) + 1):
        console.print()
        desired_item_type = console.input(f"Please insert the number of the type of items you want to keep track of ([bold green]exit[/bold green] with [bold green]0[/bold green]): ").split(" ")[0]
        console.print()

        try:
            desired_item_type_num = int(desired_item_type)
            return desired_item_type_num
        except ValueError as e:
            console.log(f"WARNING: Value {desired_item_type} is not a valid integer number, ignoring", style=WARNING_COLOR)


def get_item_type(desired_item_type_num: int) -> str:
    return ITEM_TYPES[desired_item_type_num]


'''
The following function takes a list of brands as input.
It prompts the user to select the brands they want to track by entering their corresponding numbers.
It validates the input and returns a list of selected brand numbers.

brands: A list of strings representing the brand names.
The function returns a list of integers representing the selected brand numbers.
'''
def get_desired_brand_numbers(brands: list[str]) -> list[int]:
    desired_brand_numbers = []
    
    # Get desired brand numbers
    while len(desired_brand_numbers) == 0:
        console.print()
        desired_brand_numbers = console.input(f"Please insert the numbers of the brands you want to track ([bold red]{1}[/bold red] to [bold red]{len(brands)}[/bold red] - [bold green]exit[/bold green] with [bold green]0[/bold green]): ").split(" ")
        console.print()

        desired_brand_numbers = sanitize_brand_numbers(desired_brand_numbers, len(brands))

        if len(desired_brand_numbers) == 0:
            console.log("WARNING: No valid brand numbers after sanitization", style=WARNING_COLOR)
    return desired_brand_numbers


'''
The following function displays a countdown timer in the console.
It takes the number of seconds as input and updates the timer every second.

seconds: The number of seconds for the countdown.
The function uses the rich library to create a live panel that updates the countdown.
'''
def countdown(seconds):
    with Live(refresh_per_second=2, transient=True) as live:
        while seconds >= 0:
            remaining = str(timedelta(seconds=seconds))
            live.update(Panel(f"[bold magenta]Next check in:[/bold magenta]\n[cyan]{remaining}[/cyan]"))
            time.sleep(1)
            seconds -= 1


def main():
    # Get data for telegram notifications
    telegram_credentials = get_telegram_credentials("telegram_data.json")

    # Display banner
    console.print(BANNER, style="bold red", highlight=False)

    ### ITEM TYPE SELECTION
    print_item_types()
    desired_item_type = get_desired_item_type()

    # Check if the input is valid
    while desired_item_type not in range(0, len(ITEM_TYPES) + 1):
        console.log(f"WARNING: Value not valid, please insert a valid one", style=WARNING_COLOR)
        print_item_types()
        desired_item_type = get_desired_item_type()

    # Exit if user wants to
    exit_program() if desired_item_type == 0 else None

    item_type = get_item_type(desired_item_type - 1)

    ### BRAND SELECTION
    # Fetch and prints brands
    brands = fetch_brands_list(item_type)
    print_brands_list(brands)
    desired_brand_numbers = get_desired_brand_numbers(brands)
    # Exit if user wants to
    exit_program() if 0 in desired_brand_numbers else None
    
    # Get brand names from numbers
    desired_brands = get_brand_names_from_numbers(desired_brand_numbers, brands)
    console.print()
    console.print(f"Here's the brands I'm going to keep track of for you: {desired_brands}")
    console.print()

    # Get API payloads
    payload_item_type = "CO" if item_type == "camera" else "OB"
    brands_payloads = build_payloads(brand_names=desired_brands, item_type=payload_item_type, item_status="Usato")

    ### DATA HANDLING
    # We take starting data for each brand so that we can compare it later
    original_brands_data = get_brands_data(brands_payloads)
    original_brands_dataframes = convert_to_dataframe(original_brands_data)

    # TODO: Remove this, it's just for testing purposes
    # Delete last 2 rows from each brand dataframe, to trigger the notification
    #for brand, df in original_brands_dataframes.items():
     #original_brands_dataframes[brand] = df[:-2]

    try:
        while True != False:
            # Once every SLEEP_TIME seconds
            countdown(SLEEP_TIME)

            brands_data = get_brands_data(brands_payloads)
            brands_dataframes = convert_to_dataframe(brands_data)

            for brand, df in brands_dataframes.items():
                # console.log(f"Checking new products for the brand [i][magenta]{brand}[/magenta][/i]", style=INFO_COLOR)
            
                # Get all the ids from the fresh df and check whether there is a new addition
                original_ids = original_brands_dataframes[brand].ID
                ids = df.ID
                
                # If the difference isn't the empty set, there must be a new addition
                diff_ids = set(ids) - set(original_ids)

                if len(diff_ids) > 0:
                    # WE HAVE NEW PRODUCTS
                    # Print new products
                    new_products = df[df.ID.isin(diff_ids)].copy()

                    # Merge "prezzopromozione" and "prezzovendita" so that if the promotional price is greater than 0, it replaces the original price, otherwise it keeps the original price  
                    new_products["prezzovendita"] = new_products.apply(
                        lambda row: row["prezzopromozione"] if row["prezzopromozione"] > 0 else row["prezzovendita"], axis=1
                    )
                    new_products = new_products[["marca", "modello", "prezzovendita", "stato", "prenotato"]]

                    table = get_table_from_additions(item_type, brand, new_products)

                    console.print(table)
                    
                    # Notificate to telegram
                    message = generate_message(brand, item_type, new_products)
                    send_telegram_message(message, telegram_credentials["chat_id"], telegram_credentials["api_key"])
                else:
                    if item_type == "camera":
                        console.log(f"No {item_type}s added for the brand [i][magenta]{brand}[/magenta][/i]", style=INFO_COLOR)
                    elif item_type == "lens":
                        console.log(f"No {item_type}es added for the brand [i][magenta]{brand}[/magenta][/i]", style=INFO_COLOR)
            
            # Update original data with the new one
            original_brands_data = brands_data
            original_brands_dataframes = brands_dataframes

            console.print()
    except KeyboardInterrupt:
        console.log("Scraping interrupted. See you soon, bye!", style=INFO_COLOR)

        
if __name__ == "__main__":
    main()
