import os
import requests
import json

# --- НАЛАШТУВАННЯ ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARDS_DIR = os.path.join(BASE_DIR, 'assets', 'cards')

if not os.path.exists(CARDS_DIR):
    os.makedirs(CARDS_DIR)

# Це пряме дзеркало Fan Kit
IMAGES_BASE_URL = "https://raw.githubusercontent.com/RoyaleAPI/cr-api-data/master/images/cards-75"
JSON_URL = "https://raw.githubusercontent.com/RoyaleAPI/cr-api-data/master/json/cards.json"


def format_filename(card_key, is_evo=False):
    key = card_key.replace('-', '_')
    if is_evo:
        return f"{key}_evo.png"
    return f"{key}.png"


def download_file(url, filepath):
    try:
        # User-Agent, щоб GitHub не блокував
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            return True
        return False
    except Exception as e:
        print(f"Помилка: {e}")
        return False


def download_all_assets():
    print("📡 Отримуємо список карт...")
    try:
        resp = requests.get(JSON_URL)
        cards_data = resp.json()
    except:
        print("❌ Не вдалося скачати JSON список. Перевір інтернет.")
        return

    print(f"✅ Знайдено {len(cards_data)} карт. Починаємо завантаження...")

    total_downloaded = 0
    total_evos = 0

    for card in cards_data:
        key = card["key"]  # наприклад "knight" або "golden-knight"

        # 1. Скачуємо ЗВИЧАЙНУ версію
        filename = format_filename(key, is_evo=False)
        filepath = os.path.join(CARDS_DIR, filename)

        url_normal = f"{IMAGES_BASE_URL}/{key}.png"

        # Качаємо, якщо немає
        if not os.path.exists(filepath) or os.path.getsize(filepath) < 1000:
            if download_file(url_normal, filepath):
                print(f"   📥 Card: {key}")
                total_downloaded += 1

        # 2. Скачуємо ЕВОЛЮЦІЮ (Перевіряємо суфікс -ev1)
        # У Fan Kit/RoyaleAPI еволюції називаються "knight-ev1.png"
        evo_filename = format_filename(key, is_evo=True)
        evo_filepath = os.path.join(CARDS_DIR, evo_filename)

        if not os.path.exists(evo_filepath) or os.path.getsize(evo_filepath) < 1000:
            # Формуємо URL для еволюції
            url_evo = f"{IMAGES_BASE_URL}/{key}-ev1.png"

            # Пробуємо скачати. Якщо вийде - значить еволюція існує!
            if download_file(url_evo, evo_filepath):
                print(f"   💎 EVO FOUND: {key} -> {evo_filename}")
                total_evos += 1

    print("\n" + "=" * 40)
    print(f"✨ ГОТОВО!")
    print(f"🃏 Всього карт: {total_downloaded}")
    print(f"🧬 Знайдено еволюцій: {total_evos}")
    print("Тепер у папці assets/cards є файли типу 'knight_evo.png'!")
    print("=" * 40)


if __name__ == "__main__":
    download_all_assets()