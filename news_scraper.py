import requests
from bs4 import BeautifulSoup
import json
import os
import re

NEWS_HISTORY_FILE = "news_history.json"


def clean_image_url(url):
    """
    Видаляє параметри стиснення (cdn-cgi), щоб отримати чистий оригінал.
    """
    if not url: return None
    # Видаляємо частину cdn-cgi/image/.../ щоб сервер віддав оригінал
    clean = re.sub(r'cdn-cgi/image/[^/]+/', '', url)
    return clean


def get_best_image_source(img_tag):
    """
    Магія зі скріншоту:
    RoyaleAPI ховає HD картинку в атрибути 'data-zoom-src' або 'data-src'.
    Звичайний 'src' там часто стиснений.
    """
    # 1. Найкращий варіант (Zoom версія, як на скріншоті)
    if img_tag.get('data-zoom-src'):
        return img_tag.get('data-zoom-src')

    # 2. Дуже хороший варіант (Lazy Load оригінал)
    if img_tag.get('data-src'):
        return img_tag.get('data-src')

    # 3. Звичайний варіант (якщо інших немає)
    return img_tag.get('src')


def fetch_blog_infographic(article_url, promo_filename_part):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(article_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # 1. Шукаємо контейнер id="blog_content" (як на твоєму скріншоті)
        content_div = soup.find(id="blog_content")

        # Якщо раптом id змінять, шукаємо по класу
        if not content_div:
            content_div = soup.find("div", class_="ui segment")

        if not content_div: return None

        # 2. Шукаємо всі картинки всередині тексту
        images = content_div.find_all("img")

        candidates = []

        for img in images:
            raw_url = get_best_image_source(img)
            if not raw_url: continue

            # Робимо посилання абсолютним
            if raw_url.startswith("/"):
                raw_url = "https://royaleapi.com" + raw_url

            clean_url = clean_image_url(raw_url)
            lower_url = clean_url.lower()

            # --- ФІЛЬТРИ ---

            # А. Ігноруємо сміття
            if any(x in lower_url for x in ["icon", "avatar", "logo", "badge", "social", "pixel"]):
                continue

            # Б. Ігноруємо ПРОМО (обкладинку)
            # Ми перевіряємо, чи є в назві файлу слово "promo"
            if "promo" in lower_url:
                continue

            # В. Додаткова перевірка: якщо ми знаємо назву обкладинки, ігноруємо її точну копію
            if promo_filename_part and promo_filename_part in lower_url:
                continue

            # Якщо пройшли всі фільтри — це воно!
            candidates.append(clean_url)

        # Беремо першу знайдену картинку з тексту, яка не є промо
        if candidates:
            return candidates[0]

    except Exception as e:
        print(f"Помилка пошуку інфографіки: {e}")
        return None

    return None


def get_latest_news():
    url = "https://royaleapi.com/blog"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        posts = soup.find_all("div", class_="segment")

        for post in posts:
            header = post.find("h2") or post.find("h3")
            if not header: continue

            title = header.get_text().strip()
            link_tag = post.find("a")
            if not link_tag: continue

            link = "https://royaleapi.com" + link_tag['href']

            # --- ОТРИМУЄМО ДАНІ ПРО ОБКЛАДИНКУ ---
            # Щоб знати, що ігнорувати всередині
            img_tag = post.find("img")
            promo_img = img_tag['src'] if img_tag else ""

            # Витягуємо ключову частину назви файлу промо (наприклад "s79-balance-promo")
            # Щоб випадково не взяти її ж зсередини статті
            promo_filename_part = ""
            if promo_img:
                promo_filename_part = promo_img.split("/")[-1].replace(".jpg", "").replace(".png", "")

            print(f"🔎 Новина: {title}")

            # --- ШУКАЄМО СПРАВЖНЮ ІНФОГРАФІКУ ---
            final_image = fetch_blog_infographic(link, promo_filename_part)

            if final_image:
                print(f"   ✅ Знайдено інфографіку: {final_image}")
            else:
                print("   ⚠️ Інфографіки не знайдено, беремо промо (HD).")
                # Якщо вже зовсім нічого немає, беремо обкладинку, але в HD
                final_image = clean_image_url(
                    "https://royaleapi.com" + promo_img if promo_img.startswith("/") else promo_img)

            # Зберігаємо ID (розкоментуй для роботи)
            save_news_id(link)

            return {
                "title": title,
                "link": link,
                "image": final_image
            }

    except Exception as e:
        print(f"Помилка головного парсера: {e}")
        return None


def is_news_old(news_id):
    if not os.path.exists(NEWS_HISTORY_FILE): return False
    try:
        with open(NEWS_HISTORY_FILE, "r") as f:
            history = json.load(f)
        return news_id in history
    except:
        return False


def save_news_id(news_id):
    history = []
    if os.path.exists(NEWS_HISTORY_FILE):
        with open(NEWS_HISTORY_FILE, "r") as f:
            history = json.load(f)

    if news_id not in history:
        history.append(news_id)

    if len(history) > 20: history = history[-20:]

    with open(NEWS_HISTORY_FILE, "w") as f:
        json.dump(history, f)