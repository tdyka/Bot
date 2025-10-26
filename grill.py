from telebot import types
from database import db


def show_grill_list(bot, chat_id):
    """Показує список страв гриль з бази даних"""
    grill_items = db.get_products_by_category("Гриль")

    if not grill_items:
        bot.send_message(chat_id, "Страви гриль поки недоступні")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)

    # Створюємо кнопки для кожної страви з БД
    grill_buttons = []
    for item in grill_items:
        grill_buttons.append(
            types.InlineKeyboardButton(
                item['name'],
                callback_data=f"grill_{item['id']}"
            )
        )

    for i in range(0, len(grill_buttons), 2):
        if i + 1 < len(grill_buttons):
            markup.add(grill_buttons[i], grill_buttons[i + 1])
        else:
            markup.add(grill_buttons[i])

    markup.add(types.InlineKeyboardButton("⬅️ Головне меню", callback_data="back_main"))
    bot.send_message(chat_id, "Оберіть страву гриль 🍖:", reply_markup=markup)


def send_grill_card(bot, call, grill_id):
    """Відправляє картку страви гриль з бази даних"""
    grill = db.get_product_by_id(grill_id)

    if not grill:
        bot.answer_callback_query(call.id, "❌ Страву не знайдено")
        return

    bot.answer_callback_query(call.id)

    caption = f"{grill['name']} – {grill['price']} грн\n{grill['description']}"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🛒 Додати в кошик", callback_data=f"add_cart_{grill['name']}")
    )
    markup.add(
        types.InlineKeyboardButton("🟢 Купити на сайті 🟢",
                                   url=f"https://example.com/product/{grill['name'].lower().replace(' ', '-')}"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="back_grill")
    )
    markup.add(
        types.InlineKeyboardButton("🏠 Головне меню", callback_data="back_main")
    )

    try:
        if grill['image_url']:
            bot.send_photo(
                call.message.chat.id,
                grill['image_url'],
                caption=caption,
                reply_markup=markup
            )
        else:
            bot.send_message(call.message.chat.id, caption, reply_markup=markup)
    except Exception as e:
        print(f"❌ Помилка відправки фото страви гриль: {e}")
        bot.send_message(call.message.chat.id, caption, reply_markup=markup)


def handle_grill_callback(bot, call, grill_id):
    """Обробляє callback для страв гриль з БД"""
    # Перетворюємо в int, якщо це рядок
    if isinstance(grill_id, str):
        grill_id = int(grill_id)

    # Перевіряємо, чи існує страва
    grill = db.get_product_by_id(grill_id)

    if not grill:
        bot.answer_callback_query(call.id, "❌ Страву не знайдено")
        return

    send_grill_card(bot, call, grill_id)