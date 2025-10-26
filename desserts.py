from telebot import types
from database import db


def show_dessert_list(bot, chat_id):
    """Показує список десертів з бази даних"""
    dessert_items = db.get_products_by_category("Десерти")

    if not dessert_items:
        bot.send_message(chat_id, "Десерти поки недоступні")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)

    dessert_buttons = []
    for item in dessert_items:
        dessert_buttons.append(
            types.InlineKeyboardButton(
                item['name'],
                callback_data=f"dessert_{item['id']}"
            )
        )

    for i in range(0, len(dessert_buttons), 2):
        if i + 1 < len(dessert_buttons):
            markup.add(dessert_buttons[i], dessert_buttons[i + 1])
        else:
            markup.add(dessert_buttons[i])

    markup.add(types.InlineKeyboardButton("⬅️ Головне меню", callback_data="back_main"))
    bot.send_message(chat_id, "Оберіть десерт 🍰:", reply_markup=markup)


def send_dessert_card(bot, call, dessert_id):
    """Відправляє картку десерту з бази даних"""
    dessert = db.get_product_by_id(dessert_id)

    if not dessert:
        bot.answer_callback_query(call.id, "❌ Десерт не знайдено")
        return

    bot.answer_callback_query(call.id)

    caption = f"{dessert['name']} – {dessert['price']} грн\n{dessert['description']}"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🛒 Додати в кошик", callback_data=f"add_cart_{dessert['name']}")
    )
    markup.add(
        types.InlineKeyboardButton("🟢 Купити на сайті 🟢",
                                   url=f"https://example.com/product/{dessert['name'].lower().replace(' ', '-')}"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="back_dessert")
    )
    markup.add(
        types.InlineKeyboardButton("🏠 Головне меню", callback_data="back_main")
    )

    try:
        if dessert['image_url']:
            bot.send_photo(
                call.message.chat.id,
                dessert['image_url'],
                caption=caption,
                reply_markup=markup
            )
        else:
            bot.send_message(call.message.chat.id, caption, reply_markup=markup)
    except Exception as e:
        print(f"❌ Помилка відправки фото десерту: {e}")
        bot.send_message(call.message.chat.id, caption, reply_markup=markup)


def handle_dessert_callback(bot, call, dessert_id):
    """Обробляє callback для десертів з БД"""
    # Перетворюємо в int, якщо це рядок
    if isinstance(dessert_id, str):
        dessert_id = int(dessert_id)

    dessert = db.get_product_by_id(dessert_id)

    if not dessert:
        bot.answer_callback_query(call.id, "❌ Десерт не знайдено")
        return

    send_dessert_card(bot, call, dessert_id)