# card_ids.py

def get_link_for_cards(card_names):
    """
    Генерує посилання на статистику колоди на RoyaleAPI.
    Формат: https://royaleapi.com/decks/stats/card1,card2,card3...
    """
    slugs = []
    for name in card_names:
        # 1. Прибираємо "Evolution" (RoyaleAPI саме підтягне еволюцію, якщо треба, або просто базу)
        clean_name = name.replace(" Evolution", "").strip()

        # 2. Робимо lowercase
        slug = clean_name.lower()

        # 3. Видаляємо крапки (P.E.K.K.A -> pekka)
        slug = slug.replace(".", "")

        # 4. Замінюємо пробіли на дефіси (Skeleton Army -> skeleton-army)
        slug = slug.replace(" ", "-")

        slugs.append(slug)

    if not slugs:
        return None

    # Об'єднуємо через кому
    deck_str = ",".join(slugs)

    return f"https://royaleapi.com/decks/stats/{deck_str}"