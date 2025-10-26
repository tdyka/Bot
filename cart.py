from telebot import types
from database import db

user_carts = {}


def add_to_cart(telegram_id: int, product_name: str, quantity: int = 1):
    """Додає товар в кошик"""
    product = db.get_product_by_name(product_name)
    if not product:
        return False

    if telegram_id not in user_carts:
        user_carts[telegram_id] = []

    # Перевіряємо чи товар вже в кошику
    for item in user_carts[telegram_id]:
        if item['product_id'] == product['id']:
            item['quantity'] += quantity
            return True

    # Додаємо новий товар
    user_carts[telegram_id].append({
        'product_id': product['id'],
        'name': product['name'],
        'price': product['price'],
        'quantity': quantity
    })
    return True


def remove_from_cart(telegram_id: int, product_name: str):
    """Видаляє товар з кошика"""
    if telegram_id not in user_carts:
        return False

    user_carts[telegram_id] = [
        item for item in user_carts[telegram_id]
        if item['name'] != product_name
    ]
    return True


def clear_cart(telegram_id: int):
    """Очищає кошик"""
    if telegram_id in user_carts:
        user_carts[telegram_id] = []


def get_cart(telegram_id: int):
    """Отримує кошик користувача"""
    return user_carts.get(telegram_id, [])


def get_cart_total(telegram_id: int):
    """Рахує загальну суму кошика"""
    cart = get_cart(telegram_id)
    return sum(item['price'] * item['quantity'] for item in cart)


def show_cart(bot, chat_id, telegram_id):
    """Показує кошик користувача"""
    cart = get_cart(telegram_id)

    if not cart:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🍕 До меню", callback_data="back_main")
        )
        bot.send_message(chat_id, "🛒 Ваш кошик порожній", reply_markup=markup)
        return

    # Формуємо повідомлення
    message = "🛒 Ваш кошик:\n\n"

    for item in cart:
        total_price = item['price'] * item['quantity']
        message += f"• {item['name']}\n"
        message += f"  {item['quantity']} шт × {item['price']} грн = {total_price} грн\n\n"

    total = get_cart_total(telegram_id)
    message += f"━━━━━━━━━━━━━━━\n"
    message += f"💰 Разом: {total} грн"

    markup = types.InlineKeyboardMarkup(row_width=2)

    for item in cart:
        markup.add(
            types.InlineKeyboardButton(
                f"❌ {item['name']}",
                callback_data=f"remove_{item['name']}"
            )
        )

    markup.add(
        types.InlineKeyboardButton("🗑 Очистити кошик", callback_data="clear_cart"),
        types.InlineKeyboardButton("✅ Оформити замовлення", callback_data="checkout")
    )
    markup.add(
        types.InlineKeyboardButton("⬅️ До меню", callback_data="back_main")
    )

    bot.send_message(chat_id, message, reply_markup=markup)


def show_checkout(bot, chat_id, telegram_id):
    """Показує форму оформлення замовлення"""
    cart = get_cart(telegram_id)

    if not cart:
        bot.send_message(chat_id, "Кошик порожній!")
        return

    total = get_cart_total(telegram_id)

    message = "📝 Оформлення замовлення\n\n"
    message += f"💰 Сума: {total} грн\n\n"
    message += "Виберіть спосіб оплати:"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💳 Карткою онлайн", callback_data="pay_card"),
        types.InlineKeyboardButton("💵 Готівкою при отриманні", callback_data="pay_cash")
    )
    markup.add(
        types.InlineKeyboardButton("⬅️ Назад до кошика", callback_data="view_cart")
    )

    bot.send_message(chat_id, message, reply_markup=markup)


def process_payment(bot, chat_id, telegram_id, payment_method):
    """Обробляє оплату (фейкова)"""
    cart = get_cart(telegram_id)

    if not cart:
        bot.send_message(chat_id, "Кошик порожній!")
        return

    if payment_method == "card":
        # Імітація оплати карткою
        show_fake_payment(bot, chat_id, telegram_id)
    else:
        # Готівка - одразу створюємо замовлення
        create_order_from_cart(bot, chat_id, telegram_id, "cash")


def show_fake_payment(bot, chat_id, telegram_id):
    """Показує фейкову форму оплати"""
    total = get_cart_total(telegram_id)

    message = "💳 Оплата карткою\n\n"
    message += f"💰 До сплати: {total} грн\n\n"
    message += "🔒 Безпечна оплата\n"
    message += "Введіть дані картки:\n\n"
    message += "📱 Це демонстраційна оплата\n"
    message += "Натисніть кнопку для імітації оплати"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Оплатити", callback_data="confirm_payment"),
        types.InlineKeyboardButton("❌ Скасувати", callback_data="view_cart")
    )

    bot.send_message(chat_id, message, reply_markup=markup)


def create_order_from_cart(bot, chat_id, telegram_id, payment_method):
    """Створює замовлення з кошика з автоматичною перевіркою користувача та логами"""
    import time

    cart = get_cart(telegram_id)
    if not cart:
        bot.send_message(chat_id, "Кошик порожній!")
        return

    # Додаємо користувача в БД, якщо його немає
    bot_user = bot.get_chat(telegram_id)
    db.add_user(
        telegram_id,
        username=bot_user.username if hasattr(bot_user, "username") else None,
        first_name=bot_user.first_name if hasattr(bot_user, "first_name") else None,
        last_name=bot_user.last_name if hasattr(bot_user, "last_name") else None
    )

    # Перевіряємо всі товари
    valid_items = []
    for item in cart:
        product = db.get_product_by_name(item['name'])
        if product:
            valid_items.append(item)
        else:
            bot.send_message(chat_id, f"⚠️ Товар {item['name']} не знайдено або неактивний, він буде пропущений.")

    if not valid_items:
        bot.send_message(chat_id, "❌ Усі товари неактивні або видалені.")
        return

    # Генеруємо номер замовлення
    order_number = f"ORD{int(time.time())}"

    # Лог для дебагу
    print(f"Creating order for Telegram ID: {telegram_id}")
    print(f"Order number: {order_number}")
    print(f"Items: {valid_items}")

    # Створюємо замовлення в БД
    order_id = db.create_order(telegram_id, order_number, valid_items)

    if not order_id:
        bot.send_message(chat_id, "❌ Помилка при створенні замовлення")
        return


    clear_cart(telegram_id)

    total = sum(item['price'] * item['quantity'] for item in valid_items)
    payment_text = "💳 Карткою онлайн" if payment_method == "card" else "💵 Готівкою при отриманні"

    message = "✅ Замовлення успішно оформлено!\n\n"
    message += f"📦 Номер замовлення: #{order_number}\n"
    message += f"💰 Сума: {total} грн\n"
    message += f"💳 Оплата: {payment_text}\n\n"
    message += "🔔 Ми надішлемо сповіщення про зміну статусу замовлення"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📦 Відстежити замовлення", callback_data=f"order_status_{order_number}"),
        types.InlineKeyboardButton("🏠 Головне меню", callback_data="back_main")
    )

    bot.send_message(chat_id, message, reply_markup=markup)

    from orders import simulate_delivery
    simulate_delivery(bot, order_number)


def handle_cart_callback(bot, call, action, data=None):
    """Обробляє всі callback від кошика"""
    telegram_id = call.from_user.id
    chat_id = call.message.chat.id

    if action == "view":
        bot.answer_callback_query(call.id)
        show_cart(bot, chat_id, telegram_id)

    elif action == "clear":
        clear_cart(telegram_id)
        bot.answer_callback_query(call.id, "🗑 Кошик очищено")
        show_cart(bot, chat_id, telegram_id)

    elif action == "checkout":
        bot.answer_callback_query(call.id)
        show_checkout(bot, chat_id, telegram_id)

    elif action == "pay_card":
        bot.answer_callback_query(call.id)
        process_payment(bot, chat_id, telegram_id, "card")

    elif action == "pay_cash":
        bot.answer_callback_query(call.id, "✅ Оформлюємо замовлення...")
        process_payment(bot, chat_id, telegram_id, "cash")

    elif action == "confirm_payment":
        bot.answer_callback_query(call.id, "✅ Оплата успішна!")
        create_order_from_cart(bot, chat_id, telegram_id, "card")

    elif action == "remove" and data:
        remove_from_cart(telegram_id, data)
        bot.answer_callback_query(call.id, f"❌ {data} видалено")
        show_cart(bot, chat_id, telegram_id)
