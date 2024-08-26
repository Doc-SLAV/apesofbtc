import requests
import urllib.parse
import json
import time
from tabulate import tabulate
import os
from colorama import Fore, Style, init
from datetime import datetime, timedelta
import pytz

# Inisialisasi Colorama
init(autoreset=True)

# Fungsi untuk mem-parsing x-telegram-auth menjadi dictionary
def parse_telegram_auth(auth_str):
    auth_params = dict(urllib.parse.parse_qsl(auth_str))
    user_data = urllib.parse.unquote(auth_params["user"])
    user_data = json.loads(user_data)  # Mengubah string JSON yang di-decode menjadi dictionary
    return {
        "initData": {
            "authDate": auth_params["auth_date"],
            "chatInstance": auth_params["chat_instance"],
            "chatType": auth_params["chat_type"],
            "hash": auth_params["hash"],
            "user": user_data
        }
    }

# Membaca sesi.txt untuk mendapatkan daftar x-telegram-auth
with open('sesi.txt', 'r') as file:
    auth_list = [line.strip() for line in file.readlines()]

# URL tujuan
url = "https://apes-game-be.onrender.com/tap/1"
daily_login_url = "https://apes-game-be.onrender.com/daily"
refill_energy_url = "https://apes-game-be.onrender.com/refill-energy"

# Menyimpan balance awal dari setiap token
initial_balances = {}

# Menyimpan informasi untuk tabel
results = []

# Fungsi untuk clear screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Fungsi untuk menampilkan waktu hitung mundur
def display_countdown(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

# Menentukan waktu untuk login harian
def calculate_next_daily_login(start_time):
    now = datetime.now(pytz.utc)
    next_daily_login = start_time + timedelta(days=1)
    delta = next_daily_login - now
    return max(delta.total_seconds(), 0)

# Menentukan waktu untuk refill energy
def calculate_next_refill(start_time):
    now = datetime.now(pytz.utc)
    next_refill_time = start_time + timedelta(hours=1)
    delta = next_refill_time - now
    return max(delta.total_seconds(), 0)

# Format balance to include comma as thousands separator and dot as decimal separator
def format_balance(balance):
    # Ensure balance is an integer and format it as needed
    balance_str = f"{balance / 100:,.2f}"
    return balance_str

# Logika utama
def main():
    last_daily_login_time = datetime.now(pytz.utc)
    last_refill_time = datetime.now(pytz.utc)
    daily_login_done = False
    daily_streak = "N/A"
    refill_count = 0

    while True:
        if not daily_login_done:
            # Melakukan login harian
            for auth_str in auth_list:
                data = parse_telegram_auth(auth_str)
                headers = {
                    "accept": "*/*",
                    "accept-language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                    "content-type": "application/json",
                    "x-telegram-auth": auth_str
                }
                
                try:
                    response = requests.post(daily_login_url, headers=headers, json=data)
                    response.raise_for_status()
                    daily_streak = response.json().get("dailyStreak", "N/A")
                except requests.RequestException as e:
                    print(f"{Fore.RED}Failed to fetch data for daily login: {auth_str}{Style.RESET_ALL}")
                    continue

                print(f"{Fore.GREEN}Daily login successful for token: {auth_str}{Style.RESET_ALL}")
                break
            
            last_daily_login_time = datetime.now(pytz.utc)
            daily_login_done = True

        # Melakukan refill energy jika sudah waktunya
        if refill_count < 6 and (datetime.now(pytz.utc) - last_refill_time).total_seconds() >= 3600:
            for auth_str in auth_list:
                data = parse_telegram_auth(auth_str)
                headers = {
                    "accept": "*/*",
                    "accept-language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                    "content-type": "application/json",
                    "sec-ch-ua": "\"Not-A.Brand\";v=\"99\", \"Chromium\";v=\"124\"",
                    "sec-ch-ua-mobile": "?1",
                    "sec-ch-ua-platform": "\"Android\"",
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "cross-site",
                    "x-telegram-auth": auth_str,
                    "Referer": "https://apes-game-front.onrender.com/",
                    "Referrer-Policy": "strict-origin-when-cross-origin"
                }
                
                try:
                    response = requests.post(refill_energy_url, headers=headers, json=data)
                    response.raise_for_status()
                except requests.RequestException as e:
                    print(f"{Fore.RED}Failed to fetch data for refill energy: {auth_str}{Style.RESET_ALL}")
                    continue

                print(f"{Fore.GREEN}Refill energy successful for token: {auth_str}{Style.RESET_ALL}")
                break

            refill_count += 1
            last_refill_time = datetime.now(pytz.utc)
        
        results.clear()
        for auth_str in auth_list:
            data = parse_telegram_auth(auth_str)
            headers = {
                "accept": "*/*",
                "accept-language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                "content-type": "application/json",
                "x-telegram-auth": auth_str
            }

            try:
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"{Fore.RED}Failed to fetch data for token: {auth_str}{Style.RESET_ALL}")
                continue

            result = response.json()
            username = result.get("username", "N/A")
            balance = int(result.get("balance", "0"))
            level = result.get("level", "N/A")
            energy_per_second = result.get("energyPerSecond", "N/A")
            daily_streak_value = result.get("dailyStreak", "N/A")

            if username not in initial_balances:
                initial_balances[username] = balance

            pnl = balance - initial_balances[username]
            initial_balances[username] = balance

            results.append([username, format_balance(balance), level, energy_per_second, format_balance(pnl), daily_streak_value])

        clear_screen()
        table = tabulate(results, headers=["User", "Bal", "Lvl", "E/S", "PNL", "Streak"], tablefmt="grid")
        table = table.replace("User", f"{Fore.CYAN}User{Style.RESET_ALL}")
        table = table.replace("Bal", f"{Fore.CYAN}Bal{Style.RESET_ALL}")
        table = table.replace("Lvl", f"{Fore.CYAN}Lvl{Style.RESET_ALL}")
        table = table.replace("E/S", f"{Fore.CYAN}E/S{Style.RESET_ALL}")
        table = table.replace("PNL", f"{Fore.CYAN}PNL{Style.RESET_ALL}")
        table = table.replace("Streak", f"{Fore.CYAN}Streak{Style.RESET_ALL}")

        colored_rows = []
        for line in table.splitlines():
            if line.startswith("+"):
                colored_rows.append(line)
            else:
                colored_rows.append(Fore.GREEN + line + Style.RESET_ALL)
        
        print("\n".join(colored_rows))
        
        if daily_login_done:
            seconds_until_next_daily_login = calculate_next_daily_login(last_daily_login_time)
            countdown = display_countdown(seconds_until_next_daily_login)
            print(f"\n{Fore.YELLOW}Next daily login in {countdown}{Style.RESET_ALL}")
            time.sleep(1)
            if seconds_until_next_daily_login <= 0:
                daily_login_done = False
        else:
            time.sleep(1)

if __name__ == "__main__":
    main()
