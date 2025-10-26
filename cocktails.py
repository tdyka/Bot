from telebot import types
from database import db


def show_cocktail_list(bot, chat_id):
    """Показує список коктейлів з бази даних"""
    cocktails = db.get_products_by_category("Напої")

    if not cocktails:
        bot.send_message(chat_id, "Коктейлі поки недоступні")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)

    cocktail_buttons = []
    for cocktail in cocktails:
        cocktail_buttons.append(
            types.InlineKeyboardButton(
                cocktail['name'],
                callback_data=f"cocktail_{cocktail['id']}"
            )
        )

    for i in range(0, len(cocktail_buttons), 2):
        if i + 1 < len(cocktail_buttons):
            markup.add(cocktail_buttons[i], cocktail_buttons[i + 1])
        else:
            markup.add(cocktail_buttons[i])

    markup.add(types.InlineKeyboardButton("⬅️ Головне меню", callback_data="back_main"))
    bot.send_message(chat_id, "Оберіть коктейль 🍹:", reply_markup=markup)


def send_cocktail_card(bot, call, cocktail_id):
    """Відправляє картку коктейлю з бази даних"""
    cocktail = db.get_product_by_id(cocktail_id)

    if not cocktail:
        bot.answer_callback_query(call.id, "❌ Коктейль не знайдено")
        return

    bot.answer_callback_query(call.id)

    caption = f"{cocktail['name']} – {cocktail['price']} грн\n{cocktail['description']}"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🛒 Додати в кошик", callback_data=f"add_cart_{cocktail['name']}")
    )
    markup.add(
        types.InlineKeyboardButton("🟢 Купити на сайті 🟢",
                                   url=f"https://example.com/product/{cocktail['name'].lower().replace(' ', '-')}"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="back_cocktail")
    )
    markup.add(
        types.InlineKeyboardButton("🏠 Головне меню", callback_data="back_main")
    )

    try:
        if cocktail['image_url']:
            bot.send_photo(
                call.message.chat.id,
                cocktail['image_url'],
                caption=caption,
                reply_markup=markup
            )
        else:
            bot.send_message(call.message.chat.id, caption, reply_markup=markup)
    except Exception as e:
        print(f"❌ Помилка відправки фото коктейлю: {e}")
        bot.send_message(call.message.chat.id, caption, reply_markup=markup)


def handle_cocktail_callback(bot, call, cocktail_id):
    """Обробляє callback для коктейлів з БД"""
    if isinstance(cocktail_id, str):
        cocktail_id = int(cocktail_id)

    cocktail = db.get_product_by_id(cocktail_id)

    if not cocktail:
        bot.answer_callback_query(call.id, "❌ Коктейль не знайдено")
        return

    send_cocktail_card(bot, call, cocktail_id)