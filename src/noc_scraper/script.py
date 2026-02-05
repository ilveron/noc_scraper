import os
import time
import json
import requests as http
from enum import Enum
from datetime import timedelta
from urllib.parse import quote_plus

import click
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.prompt import Prompt, IntPrompt

# --- CONFIGURATION & CONSTANTS ---
load_dotenv()
pd.set_option("future.no_silent_downcasting", True)

API_URL = "https://apinocservice.azurewebsites.net/api/products"
BASE_URL = "https://www.newoldcamera.com/_Marche.aspx"
SLEEP_TIME = 60

# Rich Console configuration
console = Console()
STYLE_WARN = "bold yellow"
STYLE_ERR = "bold red"
STYLE_INFO = "bold green"
STYLE_TITLE = "bold magenta"

BANNER = f'''
[bold red]
███╗   ██╗ ██████╗  ██████╗     ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗ 
████╗  ██║██╔═══██╗██╔════╝     ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
██╔██╗ ██║██║   ██║██║          ███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝
██║╚██╗██║██║   ██║██║          ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗
██║ ╚████║╚██████╔╝╚██████╗     ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║
╚═╝  ╚═══╝ ╚═════╝  ╚═════╝     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
[/bold red][dim]Refactored 2026[/dim]
'''

# --- ENUMS & CLASSES ---

class ItemType(Enum):
    CAMERA = ("camera", "CO", "Cameras")
    LENS = ("lens", "OB", "Lenses")

    def __init__(self, cli_name, api_code, display_name):
        self.cli_name = cli_name
        self.api_code = api_code
        self.display_name = display_name

    @staticmethod
    def from_string(value: str):
        for item in ItemType:
            if item.cli_name == value.lower():
                return item
        raise ValueError(f"Invalid item type: {value}")

class TelegramNotifier:
    def __init__(self, config_file="telegram_data.json"):
        self.creds = self._get_credentials(config_file)

    def _get_credentials(self, filename: str) -> dict:
        # Priority: Environment Variables -> JSON File
        creds = {
            "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
            "api_key": os.getenv("TELEGRAM_API_KEY")
        }
        
        # If env vars are missing, try file
        if not creds["chat_id"] or not creds["api_key"]:
            file_path = os.path.join(os.path.dirname(__file__), filename)
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r") as f:
                        file_data = json.load(f)
                        if not creds["chat_id"]: creds["chat_id"] = file_data.get("chat_id")
                        if not creds["api_key"]: creds["api_key"] = file_data.get("api_key")
                except Exception as e:
                    console.print(f"[Warning] Could not read telegram config file: {e}", style=STYLE_WARN)

        if not creds["chat_id"] or not creds["api_key"]:
            console.print("[Warning] Telegram credentials missing. Notifications disabled.", style=STYLE_WARN)
            return None
        return creds

    def send_message(self, message: str):
        if not self.creds: return
        
        url = f"https://api.telegram.org/bot{self.creds['api_key']}/sendMessage"
        payload = {
            "chat_id": self.creds['chat_id'],
            "text": message,
            "parse_mode": "HTML",
        }
        try:
            http.post(url, json=payload, timeout=10)
        except Exception as e:
            console.log(f"Error sending telegram message: {e}", style=STYLE_ERR)

    def generate_alert_message(self, brand: str, item_type: ItemType, new_products: pd.DataFrame) -> str:
        type_str = item_type.cli_name + ("s" if item_type == ItemType.CAMERA else "es")
        message = f"New <b>{type_str}</b> added for <b><i>{brand}</i></b>\nHere's a list:"
        for _, row in new_products.iterrows():
            message += f"\n    <b>{row['modello']}</b> (<i>{row['stato']}</i>) - {row['prezzovendita']}€"
        return message

class NOCMonitor:
    def __init__(self, item_type: ItemType, brands: list[str]):
        self.item_type = item_type
        self.brands = brands
        self.notifier = TelegramNotifier()
        self.previous_data: dict[str, pd.DataFrame] = {}

    def fetch_current_data(self) -> dict[str, pd.DataFrame]:
        brands_data = {}
        expected_cols = ["ID", "marca", "modello", "prezzopromozione", "prenotato", "prezzovendita", "stato"]
        
        for brand in self.brands:
            payload = f"marca={quote_plus(brand)}&tipo={self.item_type.api_code}&disponibile=M&bottega=Usato&path=Upload"
            try:
                resp = http.post(API_URL, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}, timeout=15)
                raw_data = resp.json().get("Result", [])
            except Exception as e:
                console.log(f"Error fetching {brand}: {e}", style=STYLE_ERR)
                raw_data = []

            df = pd.DataFrame(raw_data)
            
            # Normalize DataFrame
            if df.empty:
                df = pd.DataFrame(columns=expected_cols)
            else:
                # Ensure columns exist
                for col in expected_cols:
                    if col not in df.columns: df[col] = None
                df = df[expected_cols]
                # Fix boolean/numeric columns
                df["prenotato"] = df["prenotato"].replace({0: False, 1: True})
                # Handle promo price logic
                df["prezzovendita"] = df.apply(
                    lambda x: x["prezzopromozione"] if (pd.notnull(x["prezzopromozione"]) and x["prezzopromozione"] > 0) else x["prezzovendita"], 
                    axis=1
                )
            
            brands_data[brand] = df
        return brands_data

    def check_for_updates(self):
        current_data = self.fetch_current_data()
        
        # First run: just populate the cache
        if not self.previous_data:
            self.previous_data = current_data
            console.log(f"Initialized data for {len(self.brands)} brands.", style="dim")
            return

        for brand, df in current_data.items():
            old_df = self.previous_data.get(brand, pd.DataFrame())
            
            if old_df.empty and df.empty: continue
            if old_df.empty and not df.empty: 
                # Should not happen if initialized, but safe check
                self.previous_data[brand] = df
                continue

            # Identify new IDs
            old_ids = set(old_df["ID"]) if "ID" in old_df.columns else set()
            new_ids = set(df["ID"]) if "ID" in df.columns else set()
            diff_ids = new_ids - old_ids

            if diff_ids:
                new_products = df[df["ID"].isin(diff_ids)]
                self._handle_new_products(brand, new_products)
            
        # Update cache
        self.previous_data = current_data

    def _handle_new_products(self, brand: str, new_products: pd.DataFrame):
        # 1. Console Output
        table = Table(title=f"New {self.item_type.cli_name}s for {brand}", style="blue")
        table.add_column("Model", style="cyan")
        table.add_column("Price", justify="right", style="green")
        table.add_column("Status", style="white")
        
        for _, row in new_products.iterrows():
            table.add_row(row["modello"], f"{row['prezzovendita']}€", row["stato"])
        console.print(table)

        # 2. Telegram Notification
        msg = self.notifier.generate_alert_message(brand, self.item_type, new_products)
        self.notifier.send_message(msg)

# --- HELPER FUNCTIONS ---

def fetch_available_brands(item_type: ItemType) -> list[str]:
    """Scrapes the website to get the official list of brands."""
    url = f"{BASE_URL}?Tipo={item_type.api_code}&Bottega=Usato"
    try:
        r = http.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        return [a.text.strip() for a in soup.find_all("a", class_="txtelenco")]
    except Exception as e:
        console.log(f"Error fetching brands list: {e}", style=STYLE_ERR)
        return []

def interactive_item_type_selection() -> ItemType:
    """Prompt user to select item type."""
    console.print("\n[bold]Select Category:[/bold]")
    console.print(f"1. {ItemType.CAMERA.display_name}")
    console.print(f"2. {ItemType.LENS.display_name}")
    
    choice = IntPrompt.ask("Enter number", choices=["1", "2"], default=1)
    return ItemType.CAMERA if choice == 1 else ItemType.LENS

def interactive_brand_selection(available_brands: list[str]) -> list[str]:
    """Prompt user to select brands."""
    console.print(f"\n[bold]Available Brands:[/bold]")
    for idx, brand in enumerate(available_brands, 1):
        console.print(f"[red]{idx}.[/red] {brand}")

    while True:
        raw_input = Prompt.ask("\nEnter brand numbers (comma separated) or [bold]0[/bold] to exit")
        if raw_input.strip() == '0':
            console.print("Exiting...", style=STYLE_INFO)
            exit(0)
            
        selected_brands = []
        try:
            indices = [int(x.strip()) for x in raw_input.split(",") if x.strip().isdigit()]
            for idx in indices:
                if 1 <= idx <= len(available_brands):
                    brand = available_brands[idx - 1]
                    if brand not in selected_brands: selected_brands.append(brand)
            
            if selected_brands:
                return selected_brands
            console.print("[Warning] No valid selections made. Try again.", style=STYLE_WARN)
        except ValueError:
            console.print("Invalid input format.", style=STYLE_ERR)

def countdown_timer(seconds: int):
    """Visual countdown."""
    with Live(transient=True) as live:
        for rem in range(seconds, -1, -1):
            t_str = str(timedelta(seconds=rem))
            live.update(Panel(f"[bold magenta]Next check in:[/bold magenta]\n[cyan]{t_str}[/cyan]", border_style="blue"))
            time.sleep(1)

# --- MAIN COMMAND ---

@click.command()
@click.option('--type', 'cli_type', type=click.Choice(['camera', 'lens'], case_sensitive=False), help='Type of item: camera or lens')
@click.option('--brands', 'cli_brands', type=str, help='Comma separated list of brands to track (e.g. "Canon, Sony")')
def main(cli_type, cli_brands):
    console.print(BANNER, highlight=False)
    
    selected_item_type = None
    selected_brands = []

    # 1. Determine Item Type
    if cli_type:
        selected_item_type = ItemType.from_string(cli_type)
        console.print(f"CLI Mode: Tracking [cyan]{selected_item_type.display_name}[/cyan]")
    else:
        # Fallback to interactive
        selected_item_type = interactive_item_type_selection()

    # Fetch official list from website to validate or display
    available_brands = fetch_available_brands(selected_item_type)
    if not available_brands:
        console.print("Could not retrieve brand list. Aborting.", style=STYLE_ERR)
        return

    # 2. Determine Brands
    if cli_brands:
        # Clean and Validate CLI input
        user_inputs = [b.strip().lower() for b in cli_brands.split(",")]
        # Case insensitive matching against official list
        valid_map = {b.lower(): b for b in available_brands}
        
        for ui in user_inputs:
            if ui in valid_map:
                selected_brands.append(valid_map[ui])
            else:
                console.print(f"[Warning] Brand '{ui}' not found in available list. Ignoring.", style=STYLE_WARN)

        if not selected_brands:
            console.print("[bold red]No valid brands provided via CLI.[/bold red] Switching to interactive mode.", style=STYLE_WARN)
    
    # 3. Fallback to interactive if list is still empty (either no CLI args or all invalid)
    if not selected_brands:
        selected_brands = interactive_brand_selection(available_brands)

    # 4. Start Monitoring
    console.print(Panel(f"Tracking: [bold green]{', '.join(selected_brands)}[/bold green]", title="Configuration Locked"))
    
    monitor = NOCMonitor(selected_item_type, selected_brands)
    
    # Main Loop
    try:
        # Initial run
        with console.status("[bold green]Fetching initial data..."):
            monitor.check_for_updates()
            
        while True:
            countdown_timer(SLEEP_TIME)
            # console.log("Checking for updates...", style="dim")
            monitor.check_for_updates()
            
    except KeyboardInterrupt:
        console.print("\n[bold red]Stopping monitor. Goodbye![/bold red]")

if __name__ == "__main__":
    main()