from telebot import types
from database import db


def show_salad_list(bot, chat_id):
    """Показує список салатів з бази даних"""
    salad_items = db.get_products_by_category("Салати")

    if not salad_items:
        bot.send_message(chat_id, "Салати поки недоступні")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)

    # Створюємо кнопки для кожного салату з БД
    salad_buttons = []
    for item in salad_items:
        salad_buttons.append(
            types.InlineKeyboardButton(
                item['name'],
                callback_data=f"salad_{item['id']}"
            )
        )

    # Додаємо кнопки по 2 в рядок
    for i in range(0, len(salad_buttons), 2):
        if i + 1 < len(salad_buttons):
            markup.add(salad_buttons[i], salad_buttons[i + 1])
        else:
            markup.add(salad_buttons[i])

    markup.add(types.InlineKeyboardButton("⬅️ Головне меню", callback_data="back_main"))
    bot.send_message(chat_id, "Оберіть салат 🥗:", reply_markup=markup)


def send_salad_card(bot, call, salad_id):
    """Відправляє картку салату з бази даних"""
    salad = db.get_product_by_id(salad_id)

    if not salad:
        bot.answer_callback_query(call.id, "❌ Салат не знайдено")
        return

    bot.answer_callback_query(call.id)

    caption = f"{salad['name']} – {salad['price']} грн\n{salad['description']}"

    markup = types.InlineKeyboardMarkup()
    # Перший рядок: Додати в кошик
    markup.add(
        types.InlineKeyboardButton("🛒 Додати в кошик", callback_data=f"add_cart_{salad['name']}")
    )
    # Другий рядок: Купити на сайті і Назад
    markup.add(
        types.InlineKeyboardButton("🟢 Купити на сайті 🟢",
                                   url=f"https://example.com/product/{salad['name'].lower().replace(' ', '-')}"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="back_salad")
    )
    # Третій рядок: Головне меню
    markup.add(
        types.InlineKeyboardButton("🏠 Головне меню", callback_data="back_main")
    )

    try:
        if salad['image_url']:
            bot.send_photo(
                call.message.chat.id,
                salad['image_url'],
                caption=caption,
                reply_markup=markup
            )
        else:
            bot.send_message(call.message.chat.id, caption, reply_markup=markup)
    except Exception as e:
        print(f"❌ Помилка відправки фото салату: {e}")
        bot.send_message(call.message.chat.id, caption, reply_markup=markup)


def handle_salad_callback(bot, call, salad_id):
    """Обробляє callback для салатів з БД"""
    # Перетворюємо в int, якщо це рядок
    if isinstance(salad_id, str):
        salad_id = int(salad_id)

    # Перевіряємо, чи існує салат
    salad = db.get_product_by_id(salad_id)

    if not salad:
        bot.answer_callback_query(call.id, "❌ Салат не знайдено")
        return

    # Передаємо ID
    send_salad_card(bot, call, salad_id)