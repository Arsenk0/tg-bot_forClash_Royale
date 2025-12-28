import requests
import random
from bs4 import BeautifulSoup


# --- ГЕНЕРАТОРИ ПОСИЛАНЬ ---

def get_normal_url():
    """Етап 1: Шукаємо в кращих джерелах (Топ Ладдер, Гранд Челенджі)"""
    # Ми хочемо спробувати різні варіанти
    modes = ["All", "TopLadder", "GC"]
    times = ["3d", "7d"]
    sorts = ["pop", "rating"]

    m = random.choice(modes)
    t = random.choice(times)
    s = random.choice(sorts)

    # size=100 - просимо максимум
    return f"https://royaleapi.com/decks/popular?time={t}&sort={s}&size=100&players=PvP&min_trophies=0&max_trophies=10000&min_elixir=1&max_elixir=9&mode=detail&type={m}&global_exclude=false", m, s, t


def get_exclude_url():
    """Етап 2: Якщо в стандарті все старе, виключаємо популярні карти"""
    EXCLUDE_KEYS = [
        "the-log", "poison", "fireball", "zap", "arrows",
        "hog-rider", "miner", "wall-breakers", "goblin-barrel",
        "knight", "valkyrie", "skeletons", "ice-spirit", "tornado", "cannon"
    ]

    exc = random.choice(EXCLUDE_KEYS)
    print(f"🛡 Етап 2 (Hard Mode): Виключаємо карту '{exc}'...")

    return f"https://royaleapi.com/decks/popular?time=7d&sort=rating&size=100&players=PvP&min_trophies=0&max_trophies=10000&min_elixir=1&max_elixir=9&mode=detail&type=All&exc={exc}&global_exclude=false"


# Золоті слоти
HERO_AND_CHAMPIONS = {
    "Golden Knight", "Skeleton King", "Archer Queen",
    "Mighty Miner", "Monk", "Little Prince",
    "Giant", "Knight", "Mini P.E.K.K.A", "Musketeer"
}


def generate_smart_deck_name(cards):
    """Генератор назв"""
    c = set(cards)
    if {"Hog Rider", "Musketeer", "Cannon", "Ice Golem"}.issubset(c): return "Classic Hog 2.6"
    if {"Goblin Barrel", "Princess", "Rocket"}.issubset(c): return "Classic Log Bait"
    if {"X-Bow", "Tesla", "Archers"}.issubset(c): return "X-Bow 3.0"
    if {"Lava Hound", "Balloon"}.issubset(c): return "LavaLoon"
    if {"Golem", "Night Witch"}.issubset(c): return "Golem Beatdown"
    if {"P.E.K.K.A", "Battle Ram"}.issubset(c): return "PEKKA Bridge Spam"
    if {"Royal Giant", "Fisherman"}.issubset(c): return "RG Fisherman"
    if {"Electro Giant", "Tornado"}.issubset(c): return "E-Giant Mirror"
    if {"Graveyard", "Poison", "Baby Dragon"}.issubset(c): return "Splashyard"
    if {"Miner", "Wall Breakers"}.issubset(c): return "Miner WB Cycle"
    if {"Three Musketeers", "Elixir Collector"}.issubset(c): return "3M Pump"

    win_conditions = [
        ("Goblin Giant", "GobGiant"), ("Royal Giant", "Royal Giant"), ("Electro Giant", "E-Giant"),
        ("Lava Hound", "Lava"), ("Golem", "Golem"), ("Elixir Golem", "Egolem"), ("Sparky", "Sparky"),
        ("Three Musketeers", "3M"), ("Graveyard", "Graveyard"), ("Goblin Drill", "Drill"),
        ("X-Bow", "X-Bow"), ("Mortar", "Mortar"), ("Balloon", "Loon"), ("Hog Rider", "Hog"),
        ("Royal Hogs", "Royal Hogs"), ("Ram Rider", "Ram Rider"), ("Skeleton Barrel", "Skelly Barrel"),
        ("Goblin Barrel", "Log Bait"), ("Miner", "Miner"), ("Mega Knight", "Mega Knight"),
        ("P.E.K.K.A", "PEKKA"), ("Giant", "Giant"),
    ]

    primary_wc = None
    wc_name = ""
    for wc_full, wc_short in win_conditions:
        if wc_full in c:
            primary_wc = wc_full
            wc_name = wc_short
            break

    if not primary_wc: return "Meta Ladder Deck"

    suffix = ""
    if primary_wc == "Goblin Giant" and "Sparky" in c:
        suffix = "Sparky"
    elif primary_wc == "Lava Hound" and "Balloon" in c:
        suffix = "Loon"
    elif primary_wc == "Balloon" and "Miner" in c:
        return "Miner Loon Cycle"
    elif primary_wc == "Hog Rider" and "Earthquake" in c:
        suffix = "EQ"
    elif primary_wc == "Hog Rider" and "Firecracker" in c:
        suffix = "Firecracker"
    elif primary_wc == "Miner" and "Poison" in c:
        suffix = "Poison"
    elif primary_wc == "Mega Knight" and "Zap" in c:
        suffix = "Zap Bait"
    elif primary_wc == "Giant" and "Graveyard" in c:
        return "Giant Graveyard"
    elif primary_wc == "Giant" and "Sparky" in c:
        return "Giant Sparky"
    elif primary_wc == "Giant" and "Prince" in c:
        return "Giant Double Prince"
    elif primary_wc == "Goblin Barrel" and "Prince" in c:
        return "Prince Log Bait"

    if suffix: return f"{wc_name} {suffix}"

    if primary_wc in ["Hog Rider", "Miner", "Royal Hogs", "Balloon"]: return f"{wc_name} Cycle"
    if primary_wc in ["Golem", "Lava Hound", "Electro Giant", "Giant"]: return f"{wc_name} Beatdown"
    if primary_wc in ["X-Bow", "Mortar"]: return f"{wc_name} Siege"
    if primary_wc in ["Graveyard", "Goblin Drill"]: return f"{wc_name} Control"
    if primary_wc in ["Mega Knight", "P.E.K.K.A"]: return f"{wc_name} Bridge Spam"

    return f"{wc_name} Deck"


def fetch_and_parse(url):
    """Допоміжна функція"""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.find_all("div", class_="deck_segment")
    except:
        return []


def get_top_player_deck(forbidden_hashes=[], forbidden_names=[]):
    """
    1. Робить 3 спроби знайти колоду в Стандартному топі.
    2. Якщо нічого немає - робить спробу в Режимі виключення.
    """

    # --- ЕТАП 1: Наполегливий Стандарт ---
    # Ми пробуємо до 3-х разів, щоб точно переконатися, що "чесних" колод немає
    for attempt in range(3):
        url, mode, sort, time = get_normal_url()
        print(f"📡 Етап 1 (Спроба {attempt + 1}/3): {mode}, {sort}, {time}")

        decks = fetch_and_parse(url)

        if not decks:
            print("   ⚠️ Порожня відповідь сайту, пробуємо ще...")
            continue

        found_deck = process_decks(decks, forbidden_hashes, forbidden_names)

        if found_deck:
            return found_deck
        else:
            print("   ⚠️ Всі колоди з цього запиту вже були.")

    # --- ЕТАП 2: Якщо 3 спроби стандарту провалились ---
    print("\n🚨 Всі стандартні топи зайняті. Вмикаємо режим 'Exclude'...")
    url_exclude = get_exclude_url()
    decks_exclude = fetch_and_parse(url_exclude)

    return process_decks(decks_exclude, forbidden_hashes, forbidden_names)


def process_decks(all_decks, forbidden_hashes, forbidden_names):
    if not all_decks: return None

    random.shuffle(all_decks)

    for deck_div in all_decks:
        images = deck_div.select("img.deck_card_image")
        if not images: images = deck_div.find_all("img")

        parsed_cards = []
        for img in images:
            raw_name = img.get("alt") or img.get("title") or ""
            src = img.get("src", "")
            if "cards" not in src: continue

            if raw_name:
                is_evo = "evolution" in src or "Evolution" in raw_name or "-ev1" in src
                clean_name = raw_name.replace(" Evolution", "").strip()
                if not any(pc['name'] == clean_name for pc in parsed_cards):
                    parsed_cards.append({"name": clean_name, "is_evo": is_evo})

        if len(parsed_cards) == 8:
            evos = [c['name'] for c in parsed_cards if c['is_evo']]
            heroes = [c['name'] for c in parsed_cards if c['name'] in HERO_AND_CHAMPIONS and not c['is_evo']]

            final_deck_array = [None] * 8
            for i, evo in enumerate(evos[:2]): final_deck_array[i] = evo
            for i, hero in enumerate(heroes[:2]): final_deck_array[2 + i] = hero

            used = set([c for c in final_deck_array if c is not None])
            leftovers = [c['name'] for c in parsed_cards if c['name'] not in used]

            idx = 0
            for i in range(8):
                if final_deck_array[i] is None and idx < len(leftovers):
                    final_deck_array[i] = leftovers[idx]
                    idx += 1

            if None in final_deck_array: continue

            # Перевірки
            deck_hash = ",".join(sorted(final_deck_array))
            if deck_hash in forbidden_hashes: continue

            deck_name = generate_smart_deck_name(final_deck_array)
            if deck_name in forbidden_names and deck_name != "Meta Ladder Deck":
                continue

            print(f"🎉 Знайдено: {deck_name}")
            return {
                "deck_name": deck_name,
                "cards": final_deck_array,
                "evos": evos[:2],
                "heroes": heroes[:2],
                "player": "RoyaleAPI Meta"
            }

    return None