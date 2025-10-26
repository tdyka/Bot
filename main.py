import telebot
import webbrowser
from telebot import types
import os
from dotenv import load_dotenv
import logging
import pizza
import burgers
import grill
import pasta
import salads
import cocktails
import desserts
import cart
import orders
from database import db

# Налаштування логування
logging.basicConfig(
    filename='bot_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не знайдено в .env файлі!")

bot = telebot.TeleBot(BOT_TOKEN)
print("✅ Бот успішно запущено!")


# === ФУНКЦІЇ АВТОМАТИЧНОГО БЕКАПУ ===

def backup_database():
    """Функція для ручного бекапу"""
    try:
        backup_path = db.create_backup()
        if backup_path:
            print(f"✅ Створено бекап: {backup_path}")
            logging.info(f"Створено бекап: {backup_path}")
    except Exception as e:
        logging.error(f"Помилка бекапу: {e}")


# Створюємо бекап при запуску
backup_database()


# === КОМАНДИ БОТА ===

@bot.message_handler(commands=['start'])
def main(message):
    """Команда /start - вітання користувача"""
    try:
        # Додаємо користувача в БД
        db.add_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        bot.send_message(message.chat.id, f"Вітаю, {message.from_user.first_name}! 👋\n\nВикористовуйте /menu для перегляду меню.")
    except Exception as e:
        logging.error(f"Помилка в команді /start для користувача {message.from_user.id}: {e}")
        bot.send_message(message.chat.id, "❌ Виникла помилка. Спробуйте пізніше.")


@bot.message_handler(commands=['site'])
def site(message):
    try:
        webbrowser.open('https://classroom.google.com/u/1/c/ODAwNjM0NDczNDk0?hl=ru')
    except Exception as e:
        logging.error(f"Помилка відкриття сайту: {e}")


@bot.message_handler(commands=['menu'])
def menu(message):
    try:
        categories = db.get_categories()

        markup = types.InlineKeyboardMarkup(row_width=2)

        for category in categories:
            markup.add(
                types.InlineKeyboardButton(
                    f"{category['emoji']} {category['name']}",
                    callback_data=f"cat_{category['name']}"
                )
            )

        # Додаємо кнопку кошика
        cart_count = len(cart.get_cart(message.from_user.id))
        cart_text = f"🛒 Кошик ({cart_count})" if cart_count > 0 else "🛒 Кошик"

        markup.add(
            types.InlineKeyboardButton(cart_text, callback_data="view_cart"),
            types.InlineKeyboardButton("📦 Мої замовлення", callback_data="my_orders")
        )
        markup.add(types.InlineKeyboardButton("🔥 Акція «Середа»", callback_data="promo_wed"))

        bot.send_message(message.chat.id, f"{message.from_user.first_name}, оберіть категорію 👇", reply_markup=markup)
    except Exception as e:
        logging.error(f"Помилка відображення меню: {e}")
        bot.send_message(message.chat.id, "❌ Помилка завантаження меню. Спробуйте ще раз.")


@bot.message_handler(commands=['cart'])
def show_cart_command(message):
    try:
        cart.show_cart(bot, message.chat.id, message.from_user.id)
    except Exception as e:
        logging.error(f"Помилка відображення кошика для користувача {message.from_user.id}: {e}")
        bot.send_message(message.chat.id, "❌ Помилка завантаження кошика.")


@bot.message_handler(commands=['orders'])
def my_orders_command(message):
    try:
        orders.show_my_orders(bot, message.chat.id, message.from_user.id)
    except Exception as e:
        logging.error(f"Помилка відображення замовлень для користувача {message.from_user.id}: {e}")
        bot.send_message(message.chat.id, "❌ Помилка завантаження замовлень.")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Обробник всіх callback запитів"""
    try:
        # Категорії
        if call.data.startswith("cat_"):
            category = call.data.split("_", 1)[1]
            bot.answer_callback_query(call.id)

            if category == "Піца":
                pizza.show_pizza_list(bot, call.message.chat.id)
            elif category == "Бургери":
                burgers.show_burger_list(bot, call.message.chat.id)
            elif category == "Гриль":
                grill.show_grill_list(bot, call.message.chat.id)
            elif category == "Паста":
                pasta.show_pasta_list(bot, call.message.chat.id)
            elif category == "Салати":
                salads.show_salad_list(bot, call.message.chat.id)
            elif category == "Напої":
                cocktails.show_cocktail_list(bot, call.message.chat.id)
            elif category == "Десерти":
                desserts.show_dessert_list(bot, call.message.chat.id)
            else:
                bot.answer_callback_query(call.id)
                bot.send_message(call.message.chat.id,
                                 f"Поки немає товарів у категорії {category}")

        # Продукти
        elif call.data.startswith("pizza_"):
            pizza_name = call.data.split("_", 1)[1]
            pizza.handle_pizza_callback(bot, call, pizza_name)
        elif call.data.startswith("burger_"):
            burger_id = call.data.split("_", 1)[1]
            burgers.handle_burger_callback(bot, call, burger_id)
        elif call.data.startswith("grill_"):
            grill_id = call.data.split("_", 1)[1]
            grill.handle_grill_callback(bot, call, grill_id)
        elif call.data.startswith("pasta_"):
            pasta_id = call.data.split("_", 1)[1]
            pasta.handle_pasta_callback(bot, call, pasta_id)
        elif call.data.startswith("salad_"):
            salad_id = call.data.split("_", 1)[1]
            salads.handle_salad_callback(bot, call, salad_id)
        elif call.data.startswith("cocktail_"):
            cocktail_id = call.data.split("_", 1)[1]
            cocktails.handle_cocktail_callback(bot, call, cocktail_id)
        elif call.data.startswith("dessert_"):
            dessert_id = call.data.split("_", 1)[1]
            desserts.handle_dessert_callback(bot, call, dessert_id)

        # Додати в кошик
        elif call.data.startswith("add_cart_"):
            product_name = call.data.split("add_cart_", 1)[1]
            if cart.add_to_cart(call.from_user.id, product_name):
                bot.answer_callback_query(call.id, f"✅ {product_name} додано в кошик!")
            else:
                bot.answer_callback_query(call.id, "❌ Помилка додавання")

        # Видалити з кошика
        elif call.data.startswith("remove_"):
            product_name = call.data.split("remove_", 1)[1]
            cart.handle_cart_callback(bot, call, "remove", product_name)

        # Кошик
        elif call.data == "view_cart":
            cart.handle_cart_callback(bot, call, "view")
        elif call.data == "clear_cart":
            cart.handle_cart_callback(bot, call, "clear")
        elif call.data == "checkout":
            cart.handle_cart_callback(bot, call, "checkout")
        elif call.data == "pay_card":
            cart.handle_cart_callback(bot, call, "pay_card")
        elif call.data == "pay_cash":
            cart.handle_cart_callback(bot, call, "pay_cash")
        elif call.data == "confirm_payment":
            cart.handle_cart_callback(bot, call, "confirm_payment")

        # Замовлення
        elif call.data.startswith("order_"):
            parts = call.data.split("_")
            action = parts[1]
            order_number = "_".join(parts[2:])
            orders.handle_order_callback(bot, call, action, order_number)

        elif call.data == "my_orders":
            bot.answer_callback_query(call.id)
            # Видаляємо попереднє повідомлення якщо можливо
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            orders.show_my_orders(bot, call.message.chat.id, call.from_user.id)

        # Акція
        elif call.data == "promo_wed":
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id,
                             "🔥 Акція «Середа»!\nКожна друга піцца зі знижкою 50% у середу!")

        # Навігація
        elif call.data == "back_pizza":
            bot.answer_callback_query(call.id)
            pizza.show_pizza_list(bot, call.message.chat.id)
        elif call.data == "back_burger":
            bot.answer_callback_query(call.id)
            burgers.show_burger_list(bot, call.message.chat.id)
        elif call.data == "back_grill":
            bot.answer_callback_query(call.id)
            grill.show_grill_list(bot, call.message.chat.id)
        elif call.data == "back_cocktail":
            bot.answer_callback_query(call.id)
            cocktails.show_cocktail_list(bot, call.message.chat.id)
        elif call.data == "back_pasta":
            bot.answer_callback_query(call.id)
            pasta.show_pasta_list(bot, call.message.chat.id)
        elif call.data == "back_salad":
            bot.answer_callback_query(call.id)
            salads.show_salad_list(bot, call.message.chat.id)
        elif call.data == "back_dessert":
            bot.answer_callback_query(call.id)
            desserts.show_dessert_list(bot, call.message.chat.id)
        elif call.data == "back_main":
            bot.answer_callback_query(call.id)
            menu(call.message)

    except Exception as e:
        logging.error(f"Помилка обробки callback {call.data}: {e}")
        bot.answer_callback_query(call.id, "❌ Виникла помилка. Спробуйте ще раз.")


# Запускаємо бота
print("🤖 Бот працює. Натисніть Ctrl+C для зупинки.")
bot.polling(non_stop=True)