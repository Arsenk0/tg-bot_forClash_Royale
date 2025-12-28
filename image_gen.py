import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
CARDS_DIR = os.path.join(ASSETS_DIR, 'cards')
FONT_PATH = os.path.join(ASSETS_DIR, 'font.ttf')
OUTPUT_FILENAME = "deck_preview.png"

IMG_WIDTH, IMG_HEIGHT = 1000, 800
BG_COLOR = (20, 15, 35)
TEXT_COLOR = (255, 255, 255)
EVO_GLOW = (200, 0, 255)
GOLD_GLOW = (255, 215, 0)

# Кеш файлів (lower case -> real name)
EXISTING_FILES = {f.lower(): f for f in os.listdir(CARDS_DIR)}


def find_file(filename):
    if filename.lower() in EXISTING_FILES:
        return EXISTING_FILES[filename.lower()]
    return None


def get_card_filename(card_name, is_evo=False, is_hero=False):
    # Базова назва: snake_case (всі пробіли -> підкреслення)
    # Наприклад: "Royal Hogs" -> "royal_hogs"
    slug = card_name.lower().replace(' ', '_').replace('-', '_').replace('.', '')

    candidates = []

    # Пріоритет 1: Герой (пробуємо і з дефісом, і з підкресленням)
    if is_hero:
        candidates.append(f"{slug}-hero.png")  # mini_pekka-hero.png
        candidates.append(f"{slug}-hero.jpg")
        candidates.append(f"{slug}_hero.png")  # про всяк випадок

    # Пріоритет 2: Еволюція
    if is_evo:
        candidates.append(f"{slug}-evo.png")  # archers-evo.png
        candidates.append(f"{slug}_evo.png")

    # Стандарт
    candidates.append(f"{slug}.png")  # hog_rider.png
    candidates.append(f"{slug}.jpg")

    for f in candidates:
        found = find_file(f)
        if found: return found

    return f"{slug}.png"


def get_fitted_font(draw, text, font_path, max_width, start_size=90):
    size = start_size
    while size > 20:
        try:
            font = ImageFont.truetype(font_path, size)
        except:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_width: return font
        size -= 2
    return font


def add_glow(image, color, radius=25):
    if image.mode != 'RGBA': image = image.convert('RGBA')
    mask = image.split()[-1]
    glow = Image.new("RGBA", image.size, color)
    glow.putalpha(mask)
    glow = glow.filter(ImageFilter.GaussianBlur(radius))
    return glow


def create_deck_image(deck_name, card_names, evo_cards=[], hero_cards=[]):
    image = Image.new('RGB', (IMG_WIDTH, IMG_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(image)

    # Заголовок
    font = get_fitted_font(draw, deck_name, FONT_PATH, IMG_WIDTH - 60, 90)
    bbox = draw.textbbox((0, 0), deck_name, font=font)
    text_x = (IMG_WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((text_x, 50), deck_name, font=font, fill=TEXT_COLOR)

    # Сітка
    CARD_W, CARD_H = 170, 204
    GAP, MARGIN_TOP = 35, 200
    start_x = (IMG_WIDTH - ((4 * CARD_W) + (3 * GAP))) // 2

    for i, card_name in enumerate(card_names):
        if i >= 8: break
        row, col = i // 4, i % 4
        x = start_x + col * (CARD_W + GAP)
        y = MARGIN_TOP + row * (CARD_H + GAP)

        is_evo = card_name in evo_cards
        is_hero = card_name in hero_cards

        filename = get_card_filename(card_name, is_evo=is_evo, is_hero=is_hero)
        path = os.path.join(CARDS_DIR, filename)

        try:
            card_img = Image.open(path).convert("RGBA")
            card_img = card_img.resize((CARD_W, CARD_H), Image.Resampling.LANCZOS)

            # Ефекти
            if is_hero:
                glow = add_glow(card_img, GOLD_GLOW, radius=30)
                image.paste(glow, (int(x), int(y)), mask=glow)
                draw.rectangle([x - 2, y - 2, x + CARD_W + 2, y + CARD_H + 2], outline=GOLD_GLOW, width=3)
            elif is_evo:
                glow = add_glow(card_img, EVO_GLOW, radius=25)
                image.paste(glow, (int(x), int(y)), mask=glow)
            else:
                shadow = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 100))
                image.paste(shadow, (int(x) + 5, int(y) + 5), mask=shadow)

            image.paste(card_img, (int(x), int(y)), mask=card_img)

        except FileNotFoundError:
            print(f"⚠️ Файл не знайдено: {filename}")

    image.save(os.path.join(BASE_DIR, OUTPUT_FILENAME))
    print(f"✅ Зображення збережено: {OUTPUT_FILENAME}")