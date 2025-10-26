import time
import threading
from datetime import datetime
from telebot import types
from database import db

# Статуси замовлення
ORDER_STATUSES = {
    "ordered": "🆕 Замовлення оформлено",
    "confirmed": "✅ Підтверджено",
    "preparing": "👨‍🍳 Готується",
    "cooking": "🔥 Випікається",
    "ready": "✅ Готово до доставки",
    "on_way": "🚗 В дорозі",
    "delivered": "✅ Доставлено",
    "cancelled": "❌ Скасовано"
}


def create_order(user_id, order_id, items):
    """Створює нове замовлення через БД"""
    return db.create_order(user_id, order_id, items)


def update_order_status(order_id, new_status, message=None):
    """Оновлює статус замовлення в БД"""
    db.update_order_status(order_id, new_status, message)


def get_order_info(order_number):
    """Отримує інформацію про замовлення з БД"""
    return db.get_order_details(order_number)


def get_user_orders(user_id):
    """Отримує всі замовлення користувача з БД"""
    return db.get_user_orders(user_id)


def show_my_orders(bot, chat_id, user_id):
    """Показує всі замовлення користувача"""
    user_orders = get_user_orders(user_id)

    if not user_orders:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🏠 Головне меню", callback_data="back_main"))
        bot.send_message(
            chat_id,
            "📦 У вас поки немає замовлень.\n\nОформіть своє перше замовлення!",
            reply_markup=markup
        )
        return

    # Формуємо повідомлення зі списком
    message = "📦 <b>Ваші замовлення:</b>\n\n"

    markup = types.InlineKeyboardMarkup(row_width=1)

    for order in user_orders[-10:]:  # Останні 10 замовлень
        try:
            order_date = datetime.fromisoformat(order['created_at']).strftime("%d.%m.%Y %H:%M")
        except:
            order_date = "Невідома дата"

        status_emoji = {
            'ordered': '🆕', 'confirmed': '✅', 'preparing': '👨‍🍳',
            'cooking': '🔥', 'ready': '📦', 'on_way': '🚚',
            'delivered': '✅', 'cancelled': '❌'
        }

        status_text = {
            'ordered': 'Нове', 'confirmed': 'Підтверджено', 'preparing': 'Готується',
            'cooking': 'Випікається', 'ready': 'Готово', 'on_way': 'В дорозі',
            'delivered': 'Доставлено', 'cancelled': 'Скасовано'
        }

        emoji = status_emoji.get(order.get('status'), '📦')
        status = status_text.get(order.get('status'), order.get('status', 'Невідомо'))

        order_num_short = str(order['order_number'])[-8:]

        message += f"{emoji} <b>#{order_num_short}</b>\n"
        message += f"📅 {order_date}\n"
        message += f"💰 {order['total_amount']:.2f} грн\n"
        message += f"📊 {status}\n\n"

        markup.add(
            types.InlineKeyboardButton(
                f"📋 Деталі #{order_num_short}",
                callback_data=f"order_details_{order['order_number']}"
            )
        )

    markup.add(types.InlineKeyboardButton("🏠 Головне меню", callback_data="back_main"))
    bot.send_message(chat_id, message, reply_markup=markup, parse_mode='HTML')


def show_order_details(bot, chat_id, order_number):
    """Показує детальну інформацію про замовлення"""
    order = get_order_info(order_number)

    if not order:
        bot.send_message(chat_id, "❌ Замовлення не знайдено")
        return

    try:
        order_date = datetime.fromisoformat(order['created_at']).strftime("%d.%m.%Y о %H:%M")
    except:
        order_date = "Невідома дата"

    status_emoji = {
        'ordered': '🆕', 'confirmed': '✅', 'preparing': '👨‍🍳',
        'cooking': '🔥', 'ready': '📦', 'on_way': '🚚',
        'delivered': '✅', 'cancelled': '❌'
    }

    status_text = {
        'ordered': 'Нове замовлення', 'confirmed': 'Підтверджено',
        'preparing': 'Готується', 'cooking': 'Випікається',
        'ready': 'Готово до видачі', 'on_way': 'В дорозі',
        'delivered': 'Доставлено', 'cancelled': 'Скасовано'
    }

    emoji = status_emoji.get(order.get('status'), '📦')
    status = status_text.get(order.get('status'), order.get('status', 'Невідомо'))

    message = f"📋 <b>Замовлення #{order['order_number']}</b>\n\n"
    message += f"📅 <b>Дата:</b> {order_date}\n"
    message += f"📊 <b>Статус:</b> {emoji} {status}\n\n"

    message += "🛒 <b>Склад замовлення:</b>\n"
    for item in order.get('items', []):
        total_price = item['price'] * item['quantity']
        message += f"  • {item['product_name']} x{item['quantity']} = {total_price:.2f} грн\n"

    message += f"\n💰 <b>Разом:</b> {order['total_amount']:.2f} грн\n"

    # Історія статусів
    if order.get('status_history'):
        message += f"\n📜 <b>Історія замовлення:</b>\n"
        for history in order['status_history']:
            try:
                hist_date = datetime.fromisoformat(history['created_at']).strftime("%d.%m %H:%M")
            except:
                hist_date = "—"
            hist_emoji = status_emoji.get(history.get('status'), '•')
            hist_msg = history.get('message', 'Статус змінено')
            message += f"  {hist_emoji} {hist_date} - {hist_msg}\n"

    # Кнопки
    markup = types.InlineKeyboardMarkup(row_width=2)

    # Можна скасувати тільки нові або підтверджені
    if order.get('status') in ['ordered', 'confirmed']:
        markup.add(
            types.InlineKeyboardButton(
                "❌ Скасувати замовлення",
                callback_data=f"order_cancel_{order['order_number']}"
            )
        )

    markup.add(
        types.InlineKeyboardButton("◀️ До списку", callback_data="my_orders"),
        types.InlineKeyboardButton("🏠 Меню", callback_data="back_main")
    )

    bot.send_message(chat_id, message, reply_markup=markup, parse_mode='HTML')


def send_order_status(bot, order_number):
    """Відправляє поточний статус замовлення"""
    order = get_order_info(order_number)
    if not order:
        return False

    status = order.get("status", "ordered")
    status_text = ORDER_STATUSES.get(status, "Невідомий статус")

    message = f"📦 Замовлення #{order_number}\n"
    message += f"Статус: {status_text}\n\n"
    message += f"Товари:\n"
    for item in order.get("items", []):
        message += f"• {item['product_name']} x{item['quantity']} ({item['price']} грн)\n"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🔄 Оновити статус", callback_data=f"order_refresh_{order_number}"),
        types.InlineKeyboardButton("📋 Історія", callback_data=f"order_history_{order_number}")
    )
    markup.add(
        types.InlineKeyboardButton("🏠 Головне меню", callback_data="back_main")
    )

    bot.send_message(order['telegram_id'], message, reply_markup=markup)
    return True


def send_order_history(bot, call, order_number):
    """Відправляє історію замовлення"""
    order = get_order_info(order_number)
    if not order:
        bot.answer_callback_query(call.id, "Замовлення не знайдено")
        return

    message = f"📋 Історія замовлення #{order_number}\n\n"

    for entry in order.get("status_history", []):
        try:
            status_time = datetime.fromisoformat(entry["created_at"]).strftime("%d.%m %H:%M")
        except:
            status_time = "—"
        message += f"🕐 {status_time}\n"
        message += f"{entry.get('message', 'Статус змінено')}\n\n"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("⬅️ До замовлення", callback_data=f"order_details_{order_number}")
    )

    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, message, reply_markup=markup)


def handle_order_callback(bot, call, action, order_id, order_number=None):
    """Обробляє callback від кнопок замовлень"""

    if action == "details":
        show_order_details(bot, call.message.chat.id, order_id)
        bot.answer_callback_query(call.id)

    elif action == "cancel":
        # Запитуємо підтвердження
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "✅ Так, скасувати",
                callback_data=f"order_confirm_cancel_{order_id}"
            )
        )
        markup.add(
            types.InlineKeyboardButton(
                "❌ Ні, залишити",
                callback_data=f"order_details_{order_id}"
            )
        )
        bot.edit_message_text(
            f"⚠️ Ви впевнені, що хочете скасувати замовлення #{order_id}?",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif action == "confirm":
        # Підтвердження скасування
        if order_id.startswith("cancel_"):
            actual_order = order_id.replace("cancel_", "")
            order = get_order_info(actual_order)

            if order and order.get('status') in ['ordered', 'confirmed']:
                db.update_order_status(actual_order, 'cancelled', 'Замовлення скасовано користувачем')
                bot.answer_callback_query(call.id, "✅ Замовлення скасовано")
                bot.delete_message(call.message.chat.id, call.message.message_id)
                show_my_orders(bot, call.message.chat.id, call.from_user.id)
            else:
                bot.answer_callback_query(call.id, "❌ Не можна скасувати це замовлення")
        else:
            bot.answer_callback_query(call.id)

    elif action == "status":
        order = get_order_info(order_id)
        if order:
            send_order_status(bot, order_number or order_id)
            bot.answer_callback_query(call.id)
        else:
            bot.answer_callback_query(call.id, "Замовлення не знайдено")

    elif action == "refresh":
        bot.answer_callback_query(call.id, "Статус оновлено")
        show_order_details(bot, call.message.chat.id, order_number or order_id)

    elif action == "history":
        send_order_history(bot, call, order_id)


def notify_status_change(bot, order_id, new_status, message=None):
    """Сповіщає користувача про зміну статусу"""
    order = get_order_info(order_id)
    if not order:
        return

    status_emoji = {
        "preparing": "👨‍🍳",
        "cooking": "🔥",
        "ready": "✅",
        "on_way": "🚗",
        "delivered": "🎉"
    }

    emoji = status_emoji.get(new_status, "🔔")

    text = f"{emoji} Замовлення #{order_id}\n\n"
    text += message or ORDER_STATUSES.get(new_status, "Статус оновлено")

    if new_status == "delivered":
        text += "\n\n⭐️ Дякуємо за замовлення!"
        text += "\n🙏 Будемо раді вашому відгуку"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📦 Детальніше", callback_data=f"order_details_{order_id}"),
        types.InlineKeyboardButton("🏠 Головне меню", callback_data="back_main")
    )

    bot.send_message(order['telegram_id'], text, reply_markup=markup)


# Імітація доставки
def simulate_delivery(bot, order_number):
    """Імітує процес доставки замовлення"""
    statuses = [
        ("preparing", "👨‍🍳 Почали готувати ваше замовлення", 5),
        ("cooking", "🔥 Випікається в печі", 5),
        ("ready", "✅ Готово! Передаємо кур'єру", 3),
        ("on_way", "🚗 Кур'єр виїхав до вас", 5),
        ("delivered", "✅ Доставлено! Смачного!", 0)
    ]

    def update_statuses():
        for status, msg, wait_seconds in statuses:
            time.sleep(wait_seconds)
            db.update_order_status(order_number, status, msg)
            notify_status_change(bot, order_number, status, msg)

    thread = threading.Thread(target=update_statuses)
    thread.daemon = True
    thread.start()