from telebot import types
from database import db


def show_pizza_list(bot, chat_id):
    """Показує список піц з бази даних"""
    pizzas = db.get_products_by_category("Піца")

    if not pizzas:
        bot.send_message(chat_id, "Піци поки недоступні")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)

    # Створюємо кнопки для кожної піци з БД
    pizza_buttons = []
    for pizza in pizzas:
        pizza_buttons.append(
            types.InlineKeyboardButton(
                pizza['name'],
                callback_data=f"pizza_{pizza['name']}"
            )
        )

    # Додаємо кнопки по 2 в рядок
    for i in range(0, len(pizza_buttons), 2):
        if i + 1 < len(pizza_buttons):
            markup.add(pizza_buttons[i], pizza_buttons[i + 1])
        else:
            markup.add(pizza_buttons[i])

    markup.add(types.InlineKeyboardButton("⬅️ Головне меню", callback_data="back_main"))
    bot.send_message(chat_id, "Оберіть піцу 🍕:", reply_markup=markup)


def send_pizza_card(bot, call, pizza_name):
    """Відправляє картку піци з бази даних"""
    pizza = db.get_product_by_name(pizza_name)

    if not pizza:
        bot.answer_callback_query(call.id, "Піца не знайдена")
        return

    bot.answer_callback_query(call.id)

    caption = f"{pizza['name']} – {pizza['price']} грн\n{pizza['description']}"

    markup = types.InlineKeyboardMarkup()
    # Перший рядок: Додати в кошик
    markup.add(
        types.InlineKeyboardButton("🛒 Додати в кошик", callback_data=f"add_cart_{pizza['name']}")
    )
    # Другий рядок: Купити на сайті і Назад
    markup.add(
        types.InlineKeyboardButton("🟢 Купити на сайті 🟢",
                                   url=f"https://example.com/product/{pizza['name'].lower().replace(' ', '-')}"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="back_pizza")
    )
    # Третій рядок: Головне меню
    markup.add(
        types.InlineKeyboardButton("🏠 Головне меню", callback_data="back_main")
    )

    if pizza['image_url']:
        bot.send_photo(call.message.chat.id, pizza['image_url'], caption=caption, reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, caption, reply_markup=markup)


def handle_pizza_callback(bot, call, pizza_name):
    """Обробляє callback для піци з БД"""
    send_pizza_card(bot, call, pizza_name)