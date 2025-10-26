from telebot import types
from database import db


def show_pasta_list(bot, chat_id):
    """Показує список пасти з бази даних"""
    pasta_items = db.get_products_by_category("Паста")

    if not pasta_items:
        bot.send_message(chat_id, "Паста поки недоступна")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)

    pasta_buttons = []
    for item in pasta_items:
        pasta_buttons.append(
            types.InlineKeyboardButton(
                item['name'],
                callback_data=f"pasta_{item['id']}"
            )
        )

    for i in range(0, len(pasta_buttons), 2):
        if i + 1 < len(pasta_buttons):
            markup.add(pasta_buttons[i], pasta_buttons[i + 1])
        else:
            markup.add(pasta_buttons[i])

    markup.add(types.InlineKeyboardButton("⬅️ Головне меню", callback_data="back_main"))
    bot.send_message(chat_id, "Оберіть пасту 🍝:", reply_markup=markup)


def send_pasta_card(bot, call, pasta_id):
    """Відправляє картку пасти з бази даних"""
    pasta = db.get_product_by_id(pasta_id)

    if not pasta:
        bot.answer_callback_query(call.id, "❌ Пасту не знайдено")
        return

    bot.answer_callback_query(call.id)

    caption = f"{pasta['name']} – {pasta['price']} грн\n{pasta['description']}"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🛒 Додати в кошик", callback_data=f"add_cart_{pasta['name']}")
    )
    markup.add(
        types.InlineKeyboardButton("🟢 Купити на сайті 🟢",
                                   url=f"https://example.com/product/{pasta['name'].lower().replace(' ', '-')}"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="back_pasta")
    )
    markup.add(
        types.InlineKeyboardButton("🏠 Головне меню", callback_data="back_main")
    )

    try:
        if pasta['image_url']:
            bot.send_photo(
                call.message.chat.id,
                pasta['image_url'],
                caption=caption,
                reply_markup=markup
            )
        else:
            bot.send_message(call.message.chat.id, caption, reply_markup=markup)
    except Exception as e:
        print(f"❌ Помилка відправки фото пасти: {e}")
        bot.send_message(call.message.chat.id, caption, reply_markup=markup)


def handle_pasta_callback(bot, call, pasta_id):
    """Обробляє callback для пасти з БД"""
    # Перетворюємо в int, якщо це рядок
    if isinstance(pasta_id, str):
        pasta_id = int(pasta_id)

    pasta = db.get_product_by_id(pasta_id)

    if not pasta:
        bot.answer_callback_query(call.id, "❌ Пасту не знайдено")
        return

    send_pasta_card(bot, call, pasta_id)