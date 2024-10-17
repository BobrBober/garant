import telebot
from telebot import types
import uuid
import random

# Токен вашего бота
TOKEN = "7285035799:AAENtYsuRHh8Y0AoI0CB0kL7iwUUwnSCTc0"

bot = telebot.TeleBot(TOKEN)

# Словари для хранения данных
deals = {}
users = {}
user_profiles = {}
referrals = {}

# Генерация уникальной реферальной ссылки
def generate_referral_link(user_id):
    referral_code = str(uuid.uuid4())[:8]
    return f"https://t.me/ramlina_bot?start={referral_code}"

# Обработка реферальной системы при регистрации (включая рефералов второго уровня)
def handle_referral(new_user_id, referral_code):
    for user_id, user_data in user_profiles.items():
        if user_data.get("referral_code") == referral_code:
            user_profiles[user_id]["referrals"] += 1
            user_profiles[new_user_id]["invited_by"] = user_id
            user_profiles[user_id]["earned"] += 5  # Например, 5 USDT за каждого реферала

            # Начисляем за рефералов второго уровня
            if user_profiles[user_id]["invited_by"]:
                inviter_of_inviter = user_profiles[user_id]["invited_by"]
                user_profiles[inviter_of_inviter]["second_level_referrals"] += 1
                user_profiles[inviter_of_inviter]["earned"] += 2  # Например, 2 USDT за рефералов второго уровня
            break

# Симуляция платежной системы
def fake_payment(amount):
    return True

# Генерация одноразового пароля (OTP)
def send_otp(user_id):
    otp = random.randint(100000, 999999)
    user_profiles[user_id]['otp'] = otp
    bot.send_message(user_id, f"Ваш одноразовый пароль (OTP): {otp}")

# Обработчик команды /start с проверкой на реферальный код
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()

    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = message.from_user.username
        user_profiles[user_id] = {
            'username': message.from_user.username,  # Сохраняем имя пользователя
            'balance': {'RUB': 0, 'USDT': 0},
            'active_deals': [],
            'completed_deals': [],
            'deal_stats': {'total': 0, 'successful': 0, 'failed': 0},
            'commission': 3,
            'referrals': 0,
            'earned': 0,
            'referral_code': generate_referral_link(user_id),
            'invited_by': None,  # Кто пригласил
            'second_level_referrals': 0,  # Рефералы второго уровня
        }

        # Если пользователь зарегистрировался через реферальную ссылку
        if len(args) > 1:
            referral_code = args[1]
            handle_referral(user_id, referral_code)

    # Главное меню
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("👤 Профиль"), types.KeyboardButton("💼 Сделки"))
    keyboard.add(types.KeyboardButton("➕ Создать сделку"), types.KeyboardButton("👥 Рефералы"))

    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.username}! Добро пожаловать в Bleeze GARANT! 💼\n\n"
        "🤝 Честные сделки без риска. Удачных сделок! 💸\n\n"
        "Жми /start для перезапуска.",
        reply_markup=keyboard
    )

# Профиль пользователя
@bot.message_handler(func=lambda message: message.text == "👤 Профиль")
def profile(message):
    user_id = message.from_user.id
    profile_info = user_profiles.get(user_id)
    if profile_info:
        balance = profile_info['balance']
        stats = profile_info['deal_stats']
        commission = profile_info['commission']
        referral_link = profile_info['referral_code']

        profile_text = (
            f"🌟 Пользователь: @{message.from_user.username}\n"
            f"📌 Комиссия сделок: {commission}%\n\n"
            f"💰 Баланс:\n"
            f"┗ {balance['RUB']} RUB и {balance['USDT']} USDT\n"
            "—————————————\n"
            f"🎭 Кол-во сделок: {stats['total']}\n"
            f"💵 Общая сумма успешных сделок: {stats['successful']} RUB\n"
            f"💵 Общая сумма неуспешных сделок: {stats['failed']} RUB\n"
            f"💵 Сумма покупок: 0 RUB и 0 USDT\n"
            f"💵 Сумма продаж: 0 RUB и 0 USDT\n\n"
            f"🔗 Ваша реферальная ссылка: {referral_link}"
        )

        # Кнопки профиля
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("➕ Пополнение", callback_data="replenish"),
            types.InlineKeyboardButton("💸 Вывод", callback_data="withdraw"),
            types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
        )
        bot.send_message(message.chat.id, profile_text, reply_markup=keyboard)

# Пополнение баланса
@bot.callback_query_handler(func=lambda call: call.data == "replenish")
def replenish(call):
    bot.send_message(call.message.chat.id, "Введите сумму для пополнения:")
    bot.register_next_step_handler(call.message, process_replenishment)

def process_replenishment(message):
    try:
        amount = float(message.text)
        user_id = message.from_user.id
        user_profiles[user_id]['balance']['RUB'] += amount
        bot.send_message(message.chat.id, f"Ваш баланс пополнен на {amount} RUB.")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат суммы.")

# Вывод средств с OTP
@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def withdraw(call):
    send_otp(call.message.chat.id)
    bot.send_message(call.message.chat.id, "Введите OTP для подтверждения вывода:")
    bot.register_next_step_handler(call.message, confirm_withdraw)

def confirm_withdraw(message):
    user_id = message.from_user.id
    otp_input = message.text
    if otp_input == str(user_profiles[user_id].get('otp')):
        bot.send_message(message.chat.id, "OTP подтвержден. Введите сумму для вывода:")
        bot.register_next_step_handler(message, process_withdrawal)
    else:
        bot.send_message(message.chat.id, "Неверный OTP. Попробуйте снова.")

def process_withdrawal(message):
    try:
        amount = float(message.text)
        user_id = message.from_user.id
        if user_profiles[user_id]['balance']['RUB'] >= amount:
            user_profiles[user_id]['balance']['RUB'] -= amount
            bot.send_message(message.chat.id, f"Ваш вывод на {amount} RUB успешно обработан.")
        else:
            bot.send_message(message.chat.id, "Недостаточно средств на балансе.")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат суммы.")

# Реферальная программа
@bot.message_handler(func=lambda message: message.text == "👥 Рефералы")
def referral_info(message):
    user_id = message.from_user.id
    profile_info = user_profiles.get(user_id)
    if profile_info:
        referral_count = profile_info['referrals']
        second_level_count = profile_info['second_level_referrals']
        earned = profile_info['earned']

        # Уровни комиссии в зависимости от числа рефералов
        if referral_count > 20:
            commission = 0
        elif referral_count > 15:
            commission = 1.0
        elif referral_count > 10:
            commission = 1.5
        elif referral_count > 5:
            commission = 2.0
        else:
            commission = 2.5

        user_profiles[user_id]['commission'] = commission

        referral_text = (
            "📌 Bleeze GARANT - бот для честных сделок.\n"
            "Комиссия меняется в зависимости от количества рефералов:\n"
            "1-5 рефералов - 2.5%\n"
            "5-10 рефералов - 2.0%\n"
            "10-15 рефералов - 1.5%\n"
            "15-20 рефералов - 1.0%\n"
            "20+ рефералов - 0%\n\n"
            f"🌟 Количество рефералов: {referral_count}\n"
            f"🌟 Рефералы второго уровня: {second_level_count}\n"
            f"💵 Заработано: {earned} RUB"
        )

        bot.send_message(message.chat.id, referral_text)

# Сделки пользователя
@bot.message_handler(func=lambda message: message.text == "💼 Сделки")
def deal_history(message):
    user_id = message.from_user.id
    active_deals = user_profiles[user_id]['active_deals']
    completed_deals = user_profiles[user_id]['completed_deals']

    deals_text = "Ваши активные сделки:\n"
    for deal in active_deals:
        deals_text += f"#{deal['id']}: Покупатель @{deal['buyer']} - {deal['amount']} USDT\n"

    deals_text += "\nЗавершенные сделки:\n"
    for deal in completed_deals:
        deals_text += f"#{deal['id']}: Покупатель @{deal['buyer']} - {deal['amount']} USDT\n"

    bot.send_message(message.chat.id, deals_text)

# Создание сделки
@bot.message_handler(func=lambda message: message.text == "➕ Создать сделку")
def create_deal(message):
    bot.send_message(message.chat.id, "Введите сумму сделки (USDT):")
    bot.register_next_step_handler(message, process_create_deal)

def process_create_deal(message):
    try:
        amount = float(message.text)
        user_id = message.from_user.id

        # Убедитесь, что пользователь зарегистрирован в user_profiles
        if user_id not in user_profiles:
            bot.send_message(message.chat.id, "Вы не зарегистрированы. Пожалуйста, введите /start.")
            return

        deal_id = len(deals) + 1
        deals[deal_id] = {
            'id': deal_id,
            'seller': user_profiles[user_id]['username'],
            'amount': amount,
            'buyer': None,
            'status': 'в процессе'
        }

        user_profiles[user_id]['active_deals'].append(deals[deal_id])

        bot.send_message(message.chat.id, f"Сделка #{deal_id} создана на сумму {amount} USDT.")
        bot.send_message(message.chat.id, "Введите никнейм покупателя:")
        bot.register_next_step_handler(message, confirm_buyer, deal_id)
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат суммы.")

def confirm_buyer(message, deal_id):
    buyer_username = message.text
    deal = deals[deal_id]
    deal['buyer'] = buyer_username

    bot.send_message(message.chat.id, f"Сделка #{deal_id} ожидает подтверждения от @{buyer_username}.")

    # Отправляем сообщение покупателю для подтверждения
    for user_id, user_data in users.items():
        if user_data == buyer_username:
            bot.send_message(user_id, f"Сделка #{deal_id} на сумму {deal['amount']} USDT. Подтвердите сделку.", reply_markup=create_confirmation_keyboard(deal_id))

def create_confirmation_keyboard(deal_id):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("✅ Подтвердить сделку", callback_data=f"deal_confirm_{deal_id}"))
    return keyboard

# Подтверждение сделок обеими сторонами и рейтинг
@bot.callback_query_handler(func=lambda call: call.data.startswith("deal_confirm_"))
def confirm_deal(call):
    deal_id = int(call.data.split("_")[2])
    deal = deals.get(deal_id)
    if deal:
        if deal['status'] == 'в процессе':
            deal['status'] = 'ожидание подтверждения покупателя'
            bot.send_message(call.message.chat.id, f"Продавец подтвердил сделку #{deal_id}, ожидаем покупателя.")
        elif deal['status'] == 'ожидание подтверждения покупателя':
            deal['status'] = 'завершена'
            bot.send_message(call.message.chat.id, f"Сделка #{deal_id} завершена обеими сторонами.")

            # Обновление статистики и рейтинга
            seller_id = next(user_id for user_id, data in users.items() if data == deal['seller'])
            user_profiles[seller_id]['deal_stats']['successful'] += 1
            bot.send_message(call.message.chat.id, "Оцените сделку от 1 до 5:")
            bot.register_next_step_handler(call.message, process_deal_rating, deal_id)

def process_deal_rating(message, deal_id):
    try:
        rating = int(message.text)
        if 1 <= rating <= 5:
            bot.send_message(message.chat.id, f"Спасибо за оценку {rating}!")
            # Здесь можно добавить логику для хранения рейтинга
        else:
            bot.send_message(message.chat.id, "Оценка должна быть от 1 до 5.")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат оценки.")

# Запуск бота
bot.polling(none_stop=True)
