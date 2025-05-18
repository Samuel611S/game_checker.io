import requests
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter.messagebox import showerror
from dotenv import load_dotenv
import os

load_dotenv()

ITAD_API_KEY = os.getenv("ITAD_API_KEY")
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY")

watchlist = []
currency_mode = "USD"

search_results_map = {}  # Maps title -> game ID

def fetch_conversion_rate():
    try:
        response = requests.get(f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/latest/USD")
        data = response.json()
        return data["conversion_rates"].get("EGP", 1)
    except:
        showerror("Error", "Failed to fetch currency conversion rate.")
        return 1

usd_to_egp_rate = fetch_conversion_rate()

def convert_price(price_usd):
    if currency_mode == "EGP":
        return f"E£{round(price_usd * usd_to_egp_rate, 2)}"
    else:
        return f"${round(price_usd, 2)}"

# GUI setup
app = tb.Window(themename="darkly")
app.title("Game Tracker.io")
app.geometry("1800x800")
app.rowconfigure(2, weight=1)
app.rowconfigure(5, weight=0)
app.columnconfigure(0, weight=1)

# --- Widgets ---

top_frame = ttk.Frame(app)
top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
top_frame.columnconfigure(1, weight=1)

search_label = ttk.Label(top_frame, text="Game Title:")
search_label.grid(row=0, column=0, sticky="w", padx=(0,5))

search_entry = ttk.Entry(top_frame)
search_entry.grid(row=0, column=1, sticky="ew")

search_btn = ttk.Button(top_frame, text="🔍 Search Game", command=lambda: search_game())
search_btn.grid(row=0, column=2, padx=5)

currency_toggle_var = tk.BooleanVar()
currency_toggle = ttk.Checkbutton(top_frame, text="EGP Mode", variable=currency_toggle_var, command=lambda: toggle_currency(), bootstyle="success-round-toggle")
currency_toggle.grid(row=0, column=3, padx=5)

# Results Label
results_label = ttk.Label(app, text="🔎 Search Results", font=("Segoe UI", 12, "bold"))
results_label.grid(row=1, column=0, sticky="w", padx=10)

# Main content area
content_frame = ttk.Frame(app)
content_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
content_frame.rowconfigure(0, weight=1)
content_frame.columnconfigure(0, weight=1)
content_frame.columnconfigure(1, weight=2)

# --- Results List with Scrollbar ---
results_frame = ttk.Frame(content_frame)
results_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
results_frame.rowconfigure(0, weight=1)
results_frame.columnconfigure(0, weight=1)

results_box = tk.Listbox(results_frame, height=10, font=("Segoe UI", 11))
results_box.grid(row=0, column=0, sticky="nsew")

results_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=results_box.yview)
results_scroll.grid(row=0, column=1, sticky="ns")
results_box.config(yscrollcommand=results_scroll.set)

# Price output box
result_box = tk.Text(content_frame, wrap=tk.WORD, font=("Segoe UI", 10))
result_box.grid(row=0, column=1, sticky="nsew")

# Buttons
button_frame = ttk.Frame(app)
button_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

price_btn = ttk.Button(button_frame, text="💵 Check Price", command=lambda: check_price(), bootstyle="info")
price_btn.pack(side="left", padx=5)

add_btn = ttk.Button(button_frame, text="⭐ Add to Watchlist", command=lambda: add_to_watchlist(), bootstyle="warning")
add_btn.pack(side="left", padx=5)

# Watchlist Label + Frame
ttk.Label(app, text="🎯 Watchlist", font=("Segoe UI", 12, "bold")).grid(row=4, column=0, sticky="w", padx=10, pady=(10,0))
watchlist_frame = ttk.Frame(app)
watchlist_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=5)
watchlist_frame.columnconfigure(0, weight=1)

# --- Functions ---

def update_watchlist_display():
    for widget in watchlist_frame.winfo_children():
        widget.destroy()
    for title, game_id in watchlist:
        btn = ttk.Button(watchlist_frame, text=title, style="info.TButton", command=lambda gid=game_id, t=title: load_game_from_watchlist(gid, t))
        btn.pack(anchor="w", fill="x", padx=5, pady=2)

def load_game_from_watchlist(game_id, title):
    results_box.delete(0, tk.END)
    result_box.delete("1.0", tk.END)
    results_box.insert(tk.END, f"{title}||{game_id}")
    results_box.select_set(0)
    check_price()

def search_game():
    global search_results_map
    game_title = search_entry.get()
    if not game_title:
        return

    results_box.delete(0, tk.END)
    result_box.delete("1.0", tk.END)
    search_results_map.clear()

    url = "https://api.isthereanydeal.com/games/search/v1"
    params = {"key": ITAD_API_KEY, "title": game_title}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if not data:
                results_box.insert(tk.END, "No results found.")
                return
            for game in data:
                title = game["title"]
                game_id = game["id"]
                if title not in search_results_map:
                    search_results_map[title] = game_id
                    results_box.insert(tk.END, f"{title}||{game_id}")
        else:
            showerror("Error", f"Search failed. ({response.status_code})")
    except Exception as e:
        showerror("Error", str(e))


def check_price():
    result_box.delete("1.0", tk.END)
    selected = results_box.get(tk.ACTIVE)
    if "||" not in selected:
        result_box.insert(tk.END, "Please select a valid game from the list.")
        return
    title, game_id = selected.split("||")

    url = "https://api.isthereanydeal.com/games/overview/v2"
    headers = {"Content-Type": "application/json"}
    params = {"key": ITAD_API_KEY}
    body = [game_id]

    try:
        response = requests.post(url, headers=headers, params=params, json=body)
        if response.status_code == 200:
            price_data = response.json().get("prices", [])
            if not price_data:
                result_box.insert(tk.END, f"No price data available for '{title}'.")
                return

            overview = price_data[0]
            current = overview["current"]
            lowest = overview["lowest"]

            result_text = f"🎮 {title}\n\n"
            result_text += f"Store: {current['shop']['name']}\n"
            result_text += f"Current Price: {convert_price(current['price']['amount'])}\n"
            result_text += f"Regular Price: {convert_price(current['regular']['amount'])}\n"
            result_text += f"Discount: {current['cut']}%\n"

            drm = current.get("drm", [])
            if drm:
                result_text += f"DRM: {drm[0]['name']}\n"

            platform = current.get("platforms", [])
            if platform:
                result_text += f"Platform: {platform[0]['name']}\n"

            result_text += f"Link: {current['url']}\n\n"

            if lowest["price"] is not None:
                result_text += f"🔻 Lowest Price: {convert_price(lowest['price']['amount'])} ({lowest['cut']}% off)\n"
                result_text += f"Date: {lowest['timestamp'][:10]}\n"
            else:
                result_text += "🔻 Lowest Price: Not available.\n"

            result_box.insert(tk.END, result_text)
        else:
            showerror("Error", f"Failed to fetch prices. ({response.status_code})")
    except Exception as e:
        showerror("Error", str(e))

def add_to_watchlist():
    selection = results_box.get(tk.ACTIVE)
    if selection and "||" in selection:
        title, game_id = selection.split("||")
        if (title, game_id) not in watchlist:
            watchlist.append((title, game_id))
            update_watchlist_display()

def toggle_currency():
    global currency_mode
    currency_mode = "EGP" if currency_toggle_var.get() else "USD"
    check_price()

# Start app
app.mainloop()
