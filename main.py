from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Input, Static, Button, LoadingIndicator
from textual.reactive import reactive
from textual import events
from textual.message import Message

import requests
import subprocess
import os
import glob
import time

class UserInfoDisplay(Static):
    def update_info(self, username, info, presence):
        status_map = {
            0: "[dim]Offline[/]",
            1: "[green]Online[/]",
            2: "[blue]In Game[/]",
            3: "[magenta]In Studio[/]"
        }

        s = presence.get("userPresenceType", -1)
        join_date = info.get("created", "N/A")[:10] if info.get("created") else "N/A"
        last_online = presence.get("lastOnline", "N/A")[:10] if presence.get("lastOnline") else "N/A"
        place_id = presence.get("placeId", None)

        game_info = f"\n[b]Game:[/b] {presence.get('lastLocation', 'N/A')}\n[blue]https://www.roblox.com/games/{place_id}[/]" if s == 2 else f"\n[b]Last Online:[/b] {last_online}"

        self.update(
            f"[b yellow]--- User Info ---[/b]\n"
            f"[b]Username:[/b] {username}\n"
            f"[b]User ID:[/b] {info.get('id', 'N/A')}\n"
            f"[b]Display Name:[/b] {info.get('displayName', 'N/A')}\n"
            f"[b]Join Date:[/b] {join_date}\n"
            f"[b]Status:[/b] {status_map.get(s, '[red]Unknown[/]')}"
            f"{game_info}"
        )
        return place_id if s == 2 else None

class RobloxApp(App):
    CSS_PATH = None
    BINDINGS = [("q", "quit", "Quit")]

    username = reactive("")
    user_id = reactive("")
    user_info = reactive({})
    user_presence = reactive({})
    current_place_id = reactive(None)

    class JoinGameRequest(Message):
        def __init__(self, place_id: str) -> None:
            self.place_id = place_id
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("[b cyan]Roblox User Info Tool[/b]", id="title"),
            Input(placeholder="Enter Roblox username", id="username_input"),
            Button("Fetch Info", id="fetch_btn"),
            LoadingIndicator(id="loading", visible=False),
            UserInfoDisplay(id="user_info"),
            Button("Join Game", id="join_btn", disabled=True),
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#username_input").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "fetch_btn":
            username = self.query_one("#username_input").value.strip()
            self.set_user_data(username)
        elif event.button.id == "join_btn" and self.current_place_id:
            self.join_game(self.current_place_id)

    def set_user_data(self, username: str):
        self.query_one("#loading").visible = True
        self.query_one("#join_btn").disabled = True
        self.set_interval(0.1, lambda: self.fetch_data(username), pause=False, name="fetch_interval")

    def fetch_data(self, username: str):
        self.remove_timer("fetch_interval")

        uid = self.get_id(username)
        if not uid:
            self.query_one("#user_info").update("[red]User not found or error[/red]")
            self.query_one("#loading").visible = False
            return

        info = self.get_info(uid)
        presence = self.get_presence(uid)

        self.query_one("#loading").visible = False
        place_id = self.query_one(UserInfoDisplay).update_info(username, info, presence)
        self.current_place_id = place_id
        if place_id:
            self.query_one("#join_btn").disabled = False

    def join_game(self, pid: str):
        player_path = self.find_player()
        if not player_path:
            self.query_one("#user_info").update("[red]Roblox Player not found[/red]")
            return
        try:
            subprocess.run([player_path, '--app', '-t', f"roblox://placeID={pid}"], check=True)
        except Exception as e:
            self.query_one("#user_info").update(f"[red]Error launching game: {str(e)}[/red]")

    def get_id(self, username: str):
        try:
            r = requests.get(f"https://api.roblox.com/users/get-by-username?username={username}", timeout=10)
            return r.json().get("Id")
        except:
            return None

    def get_presence(self, uid: str):
        try:
            r = requests.post("https://presence.roblox.com/v1/presence/users", json={"userIds": [uid]}, timeout=10)
            return r.json().get("userPresences", [{}])[0]
        except:
            return {}

    def get_info(self, uid: str):
        try:
            return requests.get(f"https://users.roblox.com/v1/users/{uid}", timeout=10).json()
        except:
            return {}

    def find_player(self):
        l = glob.glob(r"C:\Program Files (x86)\Roblox\Versions\version-*\RobloxPlayerBeta.exe")
        return l[0] if l else ""

if __name__ == "__main__":
    RobloxApp().run()
