import html
import json
import os
import time
from datetime import datetime, timedelta
from enum import Enum
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

import click
import pandas as pd
import requests as http
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

# --- CONFIGURATION & CONSTANTS ---
load_dotenv()
pd.set_option("future.no_silent_downcasting", True)

API_URL = "https://apinocservice.azurewebsites.net/api/products"
BASE_URL = "https://www.newoldcamera.com/_Marche.aspx"
SLEEP_TIME = 60

# Rich Console styling
console = Console()
STYLE_WARN = "bold yellow"
STYLE_ERR = "bold red"
STYLE_INFO = "bold green"
STYLE_TITLE = "bold magenta"

BANNER = """
[bold red]
███╗   ██╗ ██████╗  ██████╗      ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗ 
████╗  ██║██╔═══██╗██╔════╝      ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
██╔██╗ ██║██║   ██║██║           ███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝
██║╚██╗██║██║   ██║██║           ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗
██║ ╚████║╚██████╔╝╚██████╗      ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║
╚═╝  ╚═══╝ ╚═════╝  ╚═════╝      ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
[/bold red][dim]Refactored 2026[/dim]
"""

# --- ENUMS & CLASSES ---

class ItemType(Enum):
    CAMERA = ("camera", "CO", "Cameras")
    LENS = ("lens", "OB", "Lenses")

    def __init__(self, cli_name: str, api_code: str, display_name: str):
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
    def __init__(self, config_file: str = "telegram_data.json"):
        self.creds = self._get_credentials(config_file)

    def _get_credentials(self, filename: str) -> dict | None:
        # Priority: Environment Variables -> JSON File
        creds = {
            "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
            "api_key": os.getenv("TELEGRAM_API_KEY"),
        }

        # Fallback to local JSON file if environment variables are unset
        if not creds["chat_id"] or not creds["api_key"]:
            file_path = os.path.join(os.path.dirname(__file__), filename)
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_data = json.load(f)
                        if not creds["chat_id"]:
                            creds["chat_id"] = file_data.get("chat_id")
                        if not creds["api_key"]:
                            creds["api_key"] = file_data.get("api_key")
                except Exception as e:
                    console.print(f"[Warning] Failed to read Telegram configuration file: {e}", style=STYLE_WARN)

        if not creds["chat_id"] or not creds["api_key"]:
            console.print("[Warning] Telegram credentials missing. Notifications disabled.", style=STYLE_WARN)
            return None
        return creds

    def send_message(self, message: str):
        if not self.creds:
            return

        url = f"https://api.telegram.org/bot{self.creds['api_key']}/sendMessage"
        payload = {
            "chat_id": self.creds["chat_id"],
            "text": message,
            "parse_mode": "HTML",
        }
        try:
            resp = http.post(url, json=payload, timeout=10)
            if not resp.ok:
                console.log(f"Telegram API Error ({resp.status_code}): {resp.text}", style=STYLE_ERR)
            else:
                console.log("Telegram notification sent successfully.", style=STYLE_INFO)
        except Exception as e:
            console.log(f"Connection error while sending Telegram message: {e}", style=STYLE_ERR)

    def generate_alert_messages(self, brand: str, item_type: ItemType, new_products: pd.DataFrame) -> list[str]:
        """Generates sanitized messages split into chunks under Telegram's 4096-character limit."""
        type_str = item_type.cli_name + ("s" if item_type == ItemType.CAMERA else "es")
        header = f"🚨 New <b>{type_str}</b> added for <b><i>{html.escape(brand)}</i></b>:\n"

        messages = []
        current_msg = header

        for _, row in new_products.iterrows():
            model = html.escape(str(row["modello"]))
            status = html.escape(str(row["stato"]))
            price = html.escape(str(row["prezzovendita"]))
            line = f"\n• <b>{model}</b> (<i>{status}</i>) - {price}€"

            # Split message if it nears Telegram's max payload size
            if len(current_msg) + len(line) > 3500:
                messages.append(current_msg)
                current_msg = header + line
            else:
                current_msg += line

        if current_msg:
            messages.append(current_msg)

        return messages


class NOCMonitor:
    def __init__(self, item_type: ItemType, brands: list[str]):
        self.item_type = item_type
        self.brands = brands
        self.notifier = TelegramNotifier()
        self.previous_data: dict[str, pd.DataFrame] = {}

    @staticmethod
    def is_within_working_hours() -> bool:
        """Checks if current time in Italy falls within New Old Camera store hours."""
        now = datetime.now(ZoneInfo("Europe/Rome"))
        day = now.weekday()  # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
        current_time = now.strftime("%H:%M")

        # Open Tuesday through Saturday (1 to 5)
        if not (1 <= day <= 5):
            return False

        # Store shift intervals (half an hour buffer added for safety)
        morning_start, morning_end = "9:30", "13:30"
        afternoon_start, afternoon_end = "15:00", "19:30"

        is_morning = morning_start <= current_time <= morning_end
        is_afternoon = afternoon_start <= current_time <= afternoon_end

        return is_morning or is_afternoon

    def fetch_current_data(self) -> dict[str, pd.DataFrame]:
        brands_data = {}
        expected_cols = ["ID", "marca", "modello", "prezzopromozione", "prenotato", "prezzovendita", "stato"]
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }

        for brand in self.brands:
            payload = f"marca={quote_plus(brand)}&tipo={self.item_type.api_code}&disponibile=M&bottega=Usato&path=Upload"
            try:
                resp = http.post(API_URL, data=payload, headers=headers, timeout=15)
                raw_data = resp.json().get("Result", [])
            except Exception as e:
                console.log(f"Error fetching data for brand '{brand}': {e}", style=STYLE_ERR)
                raw_data = []

            df = pd.DataFrame(raw_data)

            if df.empty:
                df = pd.DataFrame(columns=expected_cols)
            else:
                for col in expected_cols:
                    if col not in df.columns:
                        df[col] = None
                df = df[expected_cols]

                # Convert reservation flag to boolean
                df["prenotato"] = df["prenotato"].replace({0: False, 1: True})

                # Prefer promo price when active
                df["prezzovendita"] = df.apply(
                    lambda x: x["prezzopromozione"]
                    if (pd.notnull(x["prezzopromozione"]) and x["prezzopromozione"] > 0)
                    else x["prezzovendita"],
                    axis=1,
                )

            brands_data[brand] = df
        return brands_data

    def check_for_updates(self):
        current_data = self.fetch_current_data()

        # Initial run: populate cache quietly without firing alerts
        if not self.previous_data:
            self.previous_data = {b: df for b, df in current_data.items() if not df.empty}
            console.log(f"[dim]Initialized cache for {len(self.previous_data)} brands. Monitoring active...[/dim]")
            return

        for brand, df in current_data.items():
            # Avoid overwriting existing cache if a temporary network blip returned empty results
            if df.empty:
                console.log(f"[Warning] Received empty payload for {brand}. Skipping diff check.", style=STYLE_WARN)
                continue

            old_df = self.previous_data.get(brand, pd.DataFrame(columns=["ID"]))

            old_ids = set(old_df["ID"]) if "ID" in old_df.columns else set()
            new_ids = set(df["ID"]) if "ID" in df.columns else set()
            diff_ids = new_ids - old_ids

            if diff_ids:
                new_products = df[df["ID"].isin(diff_ids)]
                self._handle_new_products(brand, new_products)

            # Update cache after inspecting differences
            self.previous_data[brand] = df

    def _handle_new_products(self, brand: str, new_products: pd.DataFrame):
        # 1. Console Output
        table = Table(title=f"New {self.item_type.cli_name}s for {brand}", style="blue")
        table.add_column("Model", style="cyan")
        table.add_column("Price", justify="right", style="green")
        table.add_column("Status", style="white")

        for _, row in new_products.iterrows():
            table.add_row(str(row["modello"]), f"{row['prezzovendita']}€", str(row["stato"]))
        console.print(table)

        # 2. Telegram Notifications
        messages = self.notifier.generate_alert_messages(brand, self.item_type, new_products)
        for msg in messages:
            self.notifier.send_message(msg)
            time.sleep(1)


# --- HELPER FUNCTIONS ---

def fetch_available_brands(item_type: ItemType) -> list[str]:
    """Scrapes the website to retrieve the active list of available brands."""
    url = f"{BASE_URL}?Tipo={item_type.api_code}&Bottega=Usato"
    try:
        r = http.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        return [a.text.strip() for a in soup.find_all("a", class_="txtelenco")]
    except Exception as e:
        console.log(f"Error fetching brand list from site: {e}", style=STYLE_ERR)
        return []


def interactive_item_type_selection() -> ItemType:
    """Prompts the user to select an item category."""
    console.print("\n[bold]Select Category:[/bold]")
    console.print(f"1. {ItemType.CAMERA.display_name}")
    console.print(f"2. {ItemType.LENS.display_name}")

    choice = IntPrompt.ask("Enter number", choices=["1", "2"], default=1)
    return ItemType.CAMERA if choice == 1 else ItemType.LENS


def interactive_brand_selection(available_brands: list[str]) -> list[str]:
    """Prompts the user to select brands from the active catalog."""
    console.print("\n[bold]Available Brands:[/bold]")
    for idx, brand in enumerate(available_brands, 1):
        console.print(f"[red]{idx}.[/red] {brand}")

    while True:
        raw_input = Prompt.ask("\nEnter brand numbers (comma-separated) or [bold]0[/bold] to exit")
        if raw_input.strip() == "0":
            console.print("Exiting...", style=STYLE_INFO)
            exit(0)

        selected_brands = []
        try:
            indices = [int(x.strip()) for x in raw_input.split(",") if x.strip().isdigit()]
            for idx in indices:
                if 1 <= idx <= len(available_brands):
                    brand = available_brands[idx - 1]
                    if brand not in selected_brands:
                        selected_brands.append(brand)

            if selected_brands:
                return selected_brands
            console.print("[Warning] No valid selections made. Please try again.", style=STYLE_WARN)
        except ValueError:
            console.print("Invalid input format.", style=STYLE_ERR)


def countdown_timer(seconds: int):
    """Renders a visual live countdown in the terminal."""
    with Live(transient=True) as live:
        for rem in range(seconds, -1, -1):
            t_str = str(timedelta(seconds=rem))
            live.update(
                Panel(
                    f"[bold magenta]Next check in:[/bold magenta]\n[cyan]{t_str}[/cyan]",
                    border_style="blue",
                )
            )
            time.sleep(1)


# --- MAIN COMMAND ---

@click.command()
@click.option(
    "--type",
    "cli_type",
    type=click.Choice(["camera", "lens"], case_sensitive=False),
    help="Type of item: camera or lens",
)
@click.option(
    "--brands",
    "cli_brands",
    type=str,
    help='Comma-separated list of brands to track (e.g., "Canon, Sony")',
)
def main(cli_type, cli_brands):
    console.print(BANNER, highlight=False)

    selected_item_type = None
    selected_brands = []

    # 1. Determine Item Type
    if cli_type:
        selected_item_type = ItemType.from_string(cli_type)
        console.print(f"CLI Mode: Tracking [cyan]{selected_item_type.display_name}[/cyan]")
    else:
        selected_item_type = interactive_item_type_selection()

    # 2. Fetch official catalog list to validate or select
    available_brands = fetch_available_brands(selected_item_type)
    if not available_brands:
        console.print("Could not retrieve brand catalog. Aborting.", style=STYLE_ERR)
        return

    # 3. Determine Brands
    if cli_brands:
        user_inputs = [b.strip().lower() for b in cli_brands.split(",")]
        valid_map = {b.lower(): b for b in available_brands}

        for ui in user_inputs:
            if ui in valid_map:
                selected_brands.append(valid_map[ui])
            else:
                console.print(f"[Warning] Brand '{ui}' not recognized. Ignoring.", style=STYLE_WARN)

        if not selected_brands:
            console.print(
                "[bold red]No valid brands provided via CLI.[/bold red] Switching to interactive mode.",
                style=STYLE_WARN,
            )

    if not selected_brands:
        selected_brands = interactive_brand_selection(available_brands)

    # 4. Start Monitoring
    console.print(Panel(f"Tracking: [bold green]{', '.join(selected_brands)}[/bold green]", title="Configuration Locked"))

    monitor = NOCMonitor(selected_item_type, selected_brands)

    try:
        # Initial run: cache seeding
        with console.status("[bold green]Fetching initial data..."):
            monitor.check_for_updates()

        while True:
            if not NOCMonitor.is_within_working_hours():
                console.print(
                    "\n[dim]Outside working hours. Monitoring will resume during store hours.[/dim]",
                    style=STYLE_INFO,
                )
                time.sleep(120)  # Check time every 2 minutes
                continue
            else:
                countdown_timer(SLEEP_TIME)
                monitor.check_for_updates()

    except KeyboardInterrupt:
        console.print("\n[bold red]Stopping monitor. Goodbye![/bold red]")


if __name__ == "__main__":
    main()