import requests, subprocess, os, time, sys
from threading import Thread
from itertools import cycle
from colorama import init, Fore, Style

init(autoreset=True)

TITLE = f"""{Fore.CYAN}
████╗ ████╗████████╗████████╗██████╗
██╔═╝ ██╔═╝╚══██╔══╝╚══██╔══╝╚════██╗
██║   ██║     ██║      ██║    █████╔╝
██║   ██║     ██║      ██║    ╚═══██╗
╚═╝   ╚═╝     ╚═╝      ╚═╝   ██████╔╝
{Style.RESET_ALL}"""

class Spinner:
    def __init__(self, msg="Loading... "):
        self.spinner = cycle(['|', '/', '-', '\\'])
        self.running = False
        self.msg = msg
        self.thread = Thread(target=self.animate)

    def animate(self):
        while self.running:
            sys.stdout.write("\r" + self.msg + next(self.spinner))
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * (len(self.msg) + 2) + "\r")

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

def get_id(username):
    try:
        r = requests.get(f"https://api.roblox.com/users/get-by-username?username={username}", timeout=10)
        return r.json().get("Id")
    except:
        return None

def get_presence(uid):
    try:
        r = requests.post("https://presence.roblox.com/v1/presence/users", json={"userIds": [uid]}, timeout=10)
        return r.json().get("userPresences", [{}])[0]
    except:
        return {}

def get_info(uid):
    try:
        return requests.get(f"https://users.roblox.com/v1/users/{uid}", timeout=10).json()
    except:
        return {}

def show_info(username, info, presence):
    print(f"\n{Fore.YELLOW}--- User Info ---{Style.RESET_ALL}")
    print(Fore.GREEN + "Username: " + Style.RESET_ALL, username)
    print(Fore.GREEN + "User ID: " + Style.RESET_ALL, info.get("id", "N/A"))
    print(Fore.GREEN + "Display Name: " + Style.RESET_ALL, info.get("displayName", "N/A"))
    date = info.get("created", "N/A")[:10] if info.get("created") else "N/A"
    print(Fore.GREEN + "Join Date: " + Style.RESET_ALL, date)

    presence_type = presence.get("userPresenceType", -1)
    status = {
        0: Fore.LIGHTBLACK_EX + "Offline" + Style.RESET_ALL,
        1: Fore.LIGHTGREEN_EX + "Online" + Style.RESET_ALL,
        2: Fore.LIGHTBLUE_EX + "In Game" + Style.RESET_ALL,
        3: Fore.LIGHTMAGENTA_EX + "In Studio" + Style.RESET_ALL
    }.get(presence_type, Fore.RED + "Unknown" + Style.RESET_ALL)

    print(Fore.GREEN + "Status: " + Style.RESET_ALL, status)

    if presence_type == 2:
        print(Fore.GREEN + "Current Game: " + Style.RESET_ALL, presence.get("lastLocation", "N/A"))
        print(Fore.GREEN + "Game URL: " + Style.RESET_ALL, f"https://www.roblox.com/games/{presence.get('placeId', 'N/A')}")
    else:
        last_online = presence.get("lastOnline", "N/A")[:10] if presence.get("lastOnline") else "N/A"
        print(Fore.GREEN + "Last Online: " + Style.RESET_ALL, last_online)

def join_game(pid):
    print(Fore.YELLOW + "Joining game not supported on Termux (headless). Open this URL manually:")
    print(f"https://www.roblox.com/games/{pid}" + Style.RESET_ALL)

def main():
    print(TITLE)
    time.sleep(1)
    username = input(Fore.CYAN + "Enter user to join: " + Style.RESET_ALL)

    spinner = Spinner("Fetching ID... ")
    spinner.start()
    uid = get_id(username)
    spinner.stop()

    if not uid:
        print(Fore.RED + "User not found or error." + Style.RESET_ALL)
        return

    spinner = Spinner("Fetching info... ")
    spinner.start()
    info = get_info(uid)
    presence = get_presence(uid)
    spinner.stop()

    if info and presence:
        show_info(username, info, presence)
        if presence.get("userPresenceType") == 2:
            input(Fore.CYAN + "\nPress Enter to show game URL..." + Style.RESET_ALL)
            join_game(presence.get("placeId"))
        else:
            print(Fore.YELLOW + "\nUser not in game." + Style.RESET_ALL)
    else:
        print(Fore.RED + "Failed to retrieve user info." + Style.RESET_ALL)

if __name__ == "__main__":
    main()
