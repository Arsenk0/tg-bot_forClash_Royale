import time
import schedule
import telebot
import os
import json
import threading
import requests  # Потрібно для скачування фото
from dotenv import load_dotenv

# Імпортуємо твої модулі
from cr_api import get_top_player_deck
from image_gen import create_deck_image
from facts import get_random_fact
from news_scraper import get_latest_news
from card_ids import get_link_for_cards

# Завантажуємо налаштування з .env
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

if not BOT_TOKEN or not CHANNEL_ID:
    print("❌ ПОМИЛКА: Перевір .env файл!")
    # exit()

bot = telebot.TeleBot(BOT_TOKEN)

# --- ФАЙЛИ ---
HISTORY_FILE = "history.json"
NAMES_FILE = "history_names.json"
STATE_FILE = "bot_state.txt"
NEWS_STATE_FILE = "last_news_link.txt"  # <--- НОВИЙ ФАЙЛ ДЛЯ ПАМ'ЯТІ НОВИН


# --- ДОПОМІЖНІ ФУНКЦІЇ ---
def load_json(filename):
    if not os.path.exists(filename): return []
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except:
        return []


def save_json(filename, data):
    if len(data) > 100: data = data[-100:]
    with open(filename, "w") as f: json.dump(data, f)


def get_deck_hash(cards):
    return ",".join(sorted(cards))


def download_image(url, filename="temp_image.jpg"):
    """Скачує картинку локально, щоб уникнути помилок Telegram"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, stream=True)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"Помилка скачування: {e}")
    return False


# --- НОВИНИ (ВИПРАВЛЕНО) ---
def job_check_news():
    print("🔍 [NEWS] Перевірка новин...")
    try:
        news = get_latest_news()

        # 1. Якщо новин немає взагалі - виходимо
        if not news:
            print("   ...новин немає (scraper нічого не повернув).")
            return

        # 2. Перевіряємо, чи ми вже постили це посилання
        last_link = ""
        if os.path.exists(NEWS_STATE_FILE):
            with open(NEWS_STATE_FILE, "r") as f:
                last_link = f.read().strip()

        # Якщо посилання співпадає з тим, що у файлі — СТОП, нічого не робимо
        if news['link'] == last_link:
            print(f"   ℹ️ Пропускаємо: ця новина вже була ({news['title']})")
            return

        # 3. Якщо новина свіжа - публікуємо
        print(f"🔥 [NEWS] Нова стаття: {news['title']}")

        caption = (
            f"⚡️ **НОВИНИ CLASH ROYALE**\n\n"
            f"📰 **{news['title']}**\n\n"
            f"🔗 [Читати повну статтю]({news['link']})\n\n"
            f"#News #RoyaleAPI"
        )

        sent_success = False

        # Спробуємо скачати і відправити як файл
        if news['image'] and download_image(news['image'], "temp_news.jpg"):
            with open("temp_news.jpg", "rb") as photo:
                bot.send_photo(CHANNEL_ID, photo, caption=caption, parse_mode="Markdown")
            os.remove("temp_news.jpg")  # Прибираємо сміття
            sent_success = True
        else:
            # Якщо фото не скачалось, шлемо просто лінк
            bot.send_message(CHANNEL_ID, caption, parse_mode="Markdown")
            sent_success = True

        # 4. Записуємо посилання у файл, щоб не постити його знову
        if sent_success:
            with open(NEWS_STATE_FILE, "w") as f:
                f.write(news['link'])
            print("✅ Посилання збережено в базу.")

    except Exception as e:
        print(f"❌ [NEWS ERROR] {e}")


# --- ФАКТ ---
def post_fact():
    print("💡 [FACT] Публікація факту...")
    try:
        # Отримуємо дані
        fact_data = get_random_fact()

        # Витягуємо текст і картинку (якщо є)
        if isinstance(fact_data, (list, tuple)):
            raw_text = fact_data[0]
            fact_image_url = fact_data[1] if len(fact_data) > 1 else None
        else:
            raw_text = str(fact_data)
            fact_image_url = None

        # --- 1. ОЧИЩЕННЯ ТЕКСТУ ---
        clean_text = raw_text.replace("💡 **Факт:**", "").replace("**", "").strip()

        # --- 2. ГАРНЕ ОФОРМЛЕННЯ ---
        formatted_caption = (
            f"🧐 **Цікавинка Clash Royale**\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"{clean_text}\n\n"
            f"🤖 #ClashFact"
        )

        # --- 3. ВІДПРАВКА ---
        if fact_image_url:
            response = requests.get(fact_image_url)
            if response.status_code == 200:
                bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=response.content,
                    caption=formatted_caption,
                    parse_mode="Markdown"
                )
            else:
                bot.send_message(CHANNEL_ID, formatted_caption, parse_mode="Markdown")
        else:
            bot.send_message(CHANNEL_ID, formatted_caption, parse_mode="Markdown")

        print("✅ Факт опубліковано!")

    except Exception as e:
        print(f"❌ Помилка при публікації факту: {e}")


# --- КОЛОДА ---
def post_deck():
    print("🃏 [DECK] Пошук колоди...")
    try:
        history_hashes = load_json(HISTORY_FILE)
        history_names = load_json(NAMES_FILE)

        deck_data = None
        for i in range(5):
            print(f"   Спроба {i + 1}...")
            candidate = get_top_player_deck(forbidden_hashes=history_hashes, forbidden_names=history_names)
            if candidate:
                deck_data = candidate
                break

        if deck_data:
            p_name = deck_data['deck_name']
            cards = deck_data['cards']
            evos = deck_data['evos']
            heroes = deck_data['heroes']

            print(f"🎨 Малюємо: {p_name}")
            create_deck_image(p_name, cards, evo_cards=evos, hero_cards=heroes)

            # Генеруємо посилання на гру
            game_link = get_link_for_cards(cards)

            caption = (
                f"🔥 **{p_name}**\n\n"
                f"📊 **Топ мета колода**\n"
                f"💎 Еволюції: {', '.join(evos) if evos else '—'}\n"
                f"🏆 Герої: {', '.join(heroes) if heroes else '—'}\n\n"
            )

            if game_link:
                caption += f"🔎 [Аналіз та копіювання (RoyaleAPI)]({game_link})\n\n"

            caption += f"#Deck #ClashRoyale"

            with open("deck_preview.png", "rb") as photo:
                bot.send_photo(CHANNEL_ID, photo, caption=caption, parse_mode="Markdown")

            # Зберігаємо
            history_hashes.append(get_deck_hash(cards))
            save_json(HISTORY_FILE, history_hashes)
            if p_name != "Meta Ladder Deck":
                history_names.append(p_name)
                save_json(NAMES_FILE, history_names)

            print("✅ Колода опублікована!")
            return True
        else:
            print("⚠️ Не знайдено нової колоди.")
            return False

    except Exception as e:
        print(f"❌ [DECK ERROR] {e}")
        return False


# --- ЩОДЕННИЙ МЕНЕДЖЕР ---
def job_daily_content():
    print("⏰ [DAILY] Час контенту...")
    last_type = "fact"
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f: last_type = f.read().strip()

    if last_type == "fact":
        if post_deck():
            with open(STATE_FILE, "w") as f: f.write("deck")
    else:
        post_fact()
        with open(STATE_FILE, "w") as f:
            f.write("fact")


# --- КОМАНДИ ---
@bot.message_handler(commands=['force_news'])
def force_news(message):
    bot.reply_to(message, "🔍 Перевіряю новини...")
    job_check_news()


@bot.message_handler(commands=['force_deck'])
def force_deck(message):
    bot.reply_to(message, "🃏 Шукаю колоду...")
    post_deck()


@bot.message_handler(commands=['force_fact'])
def force_fact(message):
    bot.reply_to(message, "💡 Публікую факт...")
    post_fact()


# --- ЗАПУСК ---
def run_scheduler():
    # Запускаємо перевірку новин кожні 30 хвилин
    schedule.every(30).minutes.do(job_check_news)

    # Запускаємо основний контент (колода або факт) о 15:00
    schedule.every().day.at("13:00").do(job_daily_content)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    print("--- 🚀 БОТ ЗАПУЩЕНО ---")

    # Запускаємо планувальник в окремому потоці
    t = threading.Thread(target=run_scheduler)
    t.start()

    # Запускаємо бота
    bot.polling(none_stop=True)